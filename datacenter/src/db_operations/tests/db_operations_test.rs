#[cfg(test)]
mod tests {
    use std::sync::Arc;
    use std::time::Duration;

    use log::error;
    use neo4rs::{query, Graph};
    use serde_json::json;
    use crate::db;
    use std::fs::{self, OpenOptions};
    use std::io::Write;
    use serial_test::serial;
    use tokio::time::sleep;


    use crate::db_operations::crud::{
        create_new_relation, get_all_uuid_nodes, get_newest_uuid, get_paginated_uuids,
        get_specific_uuid_node,
    };
    use crate::db_operations::relationshipexport::export_all_with_relationships;
    use crate::db_operations::specificoperations::{
        get_nodes_in_time_range, get_nodes_with_color, get_nodes_with_energy_consume,
        get_nodes_with_energy_cost, get_nodes_with_temperature_or_humidity,
        get_temperature_humidity_at_time,
    };
    use crate::db_operations::bigfiles::process_large_json_file;


    async fn write_to_log(message: &str) {
        let mut file = OpenOptions::new()
            .create(true)
            .append(true)
            .open("test_log.txt")
            .expect("Konnte test_log.txt nicht öffnen");

        writeln!(file, "{}", message).expect("Konnte nicht in test_log.txt schreiben");
    }

    async fn get_graph() -> Arc<neo4rs::Graph> {
        let db_handler = db::get_database().await.unwrap();
        db_handler.get_test_db().await.unwrap()
    }

    

    
    async fn setup_test_node(graph: &Graph, uuid: &str, color: &str, temp: f64, hum: f64, timestamp: &str, consume: f64, cost: f64) -> bool {
        let data = json!({
            "data": [{
                "uuid": uuid,
                "color": color,
                "sensor_data": { "temperature": temp, "humidity": hum },
                "timestamp": timestamp,
                "energy_consume": consume,
                "energy_cost": cost
            }]
        });
        match create_new_relation(&data, &graph).await {
            Ok(true) => true,
            Ok(false) => {
                
                write_to_log(&format!("Setup warning: Node with UUID {} might already exist or creation returned false.", uuid)).await;
                
                get_specific_uuid_node(uuid, graph).await.is_some()
            },
            Err(e) => {
                write_to_log(&format!("Setup failed for UUID {}: {}", uuid, e)).await;
                false
            }
        }
    }

    // cleanup function
    async fn cleanup_test_data(graph: &Graph, uuid: &str, color: &str, temp: f64, hum: f64, timestamp: &str, consume: f64, cost: f64) {
      
        let q_uuid = query("MATCH (u:UUID {id: $uuid}) DETACH DELETE u").param("uuid", uuid);
        if let Err(e) = graph.run(q_uuid).await {
            error!("Cleanup: Failed to delete UUID {}: {}", uuid, e);
        }
        sleep(Duration::from_millis(5)).await;

      
        let q_color = query("MATCH (c:Color {value: $value}) DETACH DELETE c").param("value", color);
        if let Err(e) = graph.run(q_color).await {
            
            error!("Cleanup: Failed for Color {}: {}", color, e);
        }

        let q_temp = query("MATCH (t:Temperature {value: $value}) DETACH DELETE t").param("value", temp);
         if let Err(e) = graph.run(q_temp).await {
            error!("Cleanup: Failed for Temperature {}: {}", temp, e);
        }

        let q_hum = query("MATCH (h:Humidity {value: $value}) DETACH DELETE h").param("value", hum);
        if let Err(e) = graph.run(q_hum).await {
            error!("Cleanup: Failed for Humidity {}: {}", hum, e);
        }

        let q_ts = query("MATCH (ts:Timestamp {value: $value}) DETACH DELETE ts").param("value", timestamp);
        if let Err(e) = graph.run(q_ts).await {
            error!("Cleanup: Failed for Timestamp {}: {}", timestamp, e);
        }

        let q_cost = query("MATCH (ec:EnergyCost {value: $value}) DETACH DELETE ec").param("value", cost);
        if let Err(e) = graph.run(q_cost).await {
            error!("Cleanup: Failed for EnergyCost {}: {}", cost, e);
        }

        let q_consume = query("MATCH (eco:EnergyConsume {value: $value}) DETACH DELETE eco").param("value", consume);
        if let Err(e) = graph.run(q_consume).await {
            error!("Cleanup: Failed for EnergyConsume {}: {}", consume, e);
        }
    }

    // --- Tests Start Here ---

    #[tokio::test]
    #[serial]
    async fn test_empty_data() {
        let graph = get_graph().await;
        let data = json!({ "data": [] });
        let result = create_new_relation(&data, &graph).await;
        assert!(matches!(result, Ok(false)), "Should return Ok(false) for empty array. Got: {:?}", result);
    }

    #[tokio::test]
    #[serial]
    async fn test_invalid_data() {
        let graph = get_graph().await;
        let data = json!({
            "data": [{
                "color": "red", 
                "sensor_data": { "temperature": 25.5, "humidity": 30.0 },
                "timestamp": "2023-10-01T00:00:00Z",
                "energy_consume": 100.0,
                "energy_cost": 50.0

            }]
        });
        let result = create_new_relation(&data, &graph).await;
        assert!(result.is_err(), "Should return Err for invalid data (missing UUID)");
    }

    #[tokio::test]
    #[serial]
    async fn test_valid_data() {
        let graph = get_graph().await;
        let test_uuid = "test-uuid-validate";
        let test_color = "test-color-validate";
        let test_temp = 25555.5;
        let test_hum = 3000.0;
        let test_ts = "2100-10-01T00:00:00Z";
        let test_consume = 10000.0;
        let test_cost = 50000.0;

        let data = json!({
            "data": [{
                "uuid": test_uuid,
                "color": test_color,
                "sensor_data": {
                    "temperature": test_temp,
                    "humidity": test_hum
                },
                "timestamp": test_ts,
                "energy_consume": test_consume,
                "energy_cost": test_cost
            }]
        });
        let result = create_new_relation(&data, &graph).await;
        assert!(matches!(result, Ok(true)), "Should return Ok(true) for valid data. Got: {:?}", result);

        cleanup_test_data(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_duplicate_uuid() {
        let graph = get_graph().await;
        let test_uuid = "test-uuid-duplicate";
        let test_color = "test-color-duplicate";
        let test_temp = 25555.6; 
        let test_hum = 3000.1;
        let test_ts = "2100-10-02T00:00:00Z";
        let test_consume = 10000.1;
        let test_cost = 50000.1;

        let data = json!({
            "data": [{
                "uuid": test_uuid,
                "color": test_color,
                "sensor_data": { "temperature": test_temp, "humidity": test_hum },
                "timestamp": test_ts,
                "energy_consume": test_consume,
                "energy_cost": test_cost
            }]
        });

        let first_result = create_new_relation(&data, &graph).await;
        assert!(matches!(first_result, Ok(true)), "First insertion should return Ok(true). Got: {:?}", first_result);

        
        let second_result = create_new_relation(&data, &graph).await;
        assert!(matches!(second_result, Ok(false)), "Second insertion should return Ok(false) for duplicate UUID. Got: {:?}", second_result);

        cleanup_test_data(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_serialization_error() {
        let graph = get_graph().await;
        let test_uuid = "test-uuid-serialize-err"; 

        let data = json!({
            "data": [{
                "uuid": test_uuid,
                "color": "test-color-serialize-err",
                "sensor_data": {
                    "temperature": f64::NAN, 
                    "humidity": 30.0
                },
                "timestamp": "2100-10-03T00:00:00Z",
                "energy_consume": 100.0,
                "energy_cost": 50.0
            }]
        });

        let result = create_new_relation(&data, &graph).await;
        let is_error = result.is_err();

        write_to_log(&format!(
            "Test for serialization error returned: {:?}, is_error: {}",
             result, is_error
        ))
        .await;
        assert!(is_error, "Should return Err for serialization error (NaN)");
       
    }

    #[tokio::test]
    #[serial]
    async fn test_export_all_with_relationships() {
        let graph = get_graph().await;
        let test_uuid = "test-uuid-export";
        let test_color = "test-color-export";
        let test_temp = 25555.7;
        let test_hum = 3000.2;
        let test_ts = "2100-10-04T00:00:00Z";
        let test_consume = 10000.2;
        let test_cost = 50000.2;

     
        assert!(setup_test_node(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await, "Setup failed for export test");

        let result = export_all_with_relationships(&graph, Some(100)).await;
        assert!(result.is_some(), "Export function should return Some(Value)");

        let json_result = result.unwrap();
        let output = json_result.to_string();
        fs::write("export_all_data.json", &output).expect("Fehler beim Schreiben der JSON-Datei");
        assert!(!output.is_empty(), "Exported JSON should not be empty");
        assert!(output.contains(test_uuid), "Exported JSON should contain the test UUID");

        cleanup_test_data(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_get_specific_uuid_node() {
        let graph = get_graph().await;
        let test_uuid = "test-uuid-specific";
        let test_color = "test-color-specific";
        let test_temp = 25555.8;
        let test_hum = 3000.3;
        let test_ts = "2100-10-05T00:00:00Z";
        let test_consume = 10000.3;
        let test_cost = 50000.3;

        assert!(setup_test_node(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await, "Setup failed for get specific node test");

        let start_time = std::time::Instant::now();
        let result = get_specific_uuid_node(test_uuid, &graph).await;
        let elapsed = start_time.elapsed();

        let test_succeeded = result.is_some();
        write_to_log(&format!(
            "Test for getting a node with uuid: execution time: {:?}, returned: {:?}, success: {}",
            elapsed, result, test_succeeded
        )).await;

        assert!(test_succeeded, "Should return Some(Value) for specific UUID. Got: None");
        if let Some(node) = result {
            assert_eq!(node["uuid"].as_str(), Some(test_uuid));
            assert_eq!(node["color"].as_str(), Some(test_color));
            assert_eq!(node["sensor_data"]["temperature"].as_f64(), Some(test_temp));
         
        }

        cleanup_test_data(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_get_paginated_uuids() {
        let graph = get_graph().await;
        let test_uuid = "test-uuid-paginate";
        let test_color = "test-color-paginate";
        let test_temp = 25555.9;
        let test_hum = 3000.4;
        let test_ts = "2100-10-06T00:00:00Z";
        let test_consume = 10000.4;
        let test_cost = 50000.4;

       
        assert!(setup_test_node(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await, "Setup failed for pagination test");

        let first_page_result = get_paginated_uuids(&graph, 0).await;
        assert!(first_page_result.is_some(), "Should return Some(Value) for first page");

        let first_page = first_page_result.unwrap();
        let nodes = first_page["nodes"].as_array().expect("Expected 'nodes' field to be an array");
        let total_count = first_page["pagination"]["total_count"].as_u64().unwrap() as usize;
        let total_pages = first_page["pagination"]["total_pages"].as_u64().unwrap() as usize;
        let current_page = first_page["pagination"]["current_page"].as_u64().unwrap() as usize;
        let page_size = first_page["pagination"]["page_size"].as_u64().unwrap() as usize;

        assert_eq!(current_page, 0, "Current page should be 0");
        assert_eq!(page_size, 25, "Page size should be 25"); 
        assert!(total_count > 0, "Total count should be greater than 0 after setup");

        write_to_log(&format!(
            "Pagination test - Total count: {}, Total pages: {}, First page Nodes: {}",
            total_count, total_pages, nodes.len()
        )).await;

        let expected_first_page_count = std::cmp::min(page_size, total_count);
        assert_eq!(nodes.len(), expected_first_page_count, "First page should contain the expected number of nodes");

        // Test requesting a page beyond the total pages
        if total_pages > 0 {
             let out_of_bounds_page = total_pages; 
             let empty_page_result = get_paginated_uuids(&graph, out_of_bounds_page).await;
             assert!(empty_page_result.is_some(), "Requesting out-of-bounds page should return Some");
             let empty_page = empty_page_result.unwrap();
             assert!(empty_page["nodes"].as_array().unwrap().is_empty(), "Out-of-bounds page should have no nodes");
             assert_eq!(empty_page["pagination"]["current_page"].as_u64().unwrap() as usize, out_of_bounds_page);
             assert_eq!(empty_page["pagination"]["total_pages"].as_u64().unwrap() as usize, total_pages);
        }


        cleanup_test_data(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await;
    }

    

    #[tokio::test]
    #[serial]
    async fn test_get_all_uuid_nodes() {
        let graph = get_graph().await;
        let test_uuid = "test-uuid-getall";
        let test_color = "test-color-getall";
        let test_temp = 25556.0;
        let test_hum = 3000.5;
        let test_ts = "2100-10-07T00:00:00Z";
        let test_consume = 10000.5;
        let test_cost = 50000.5;

        assert!(setup_test_node(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await, "Setup failed for get all nodes test");

        let result = get_all_uuid_nodes(&graph).await;
        assert!(result.is_some(), "get_all_uuid_nodes should return Some(Value)");

        let nodes = result.unwrap();
        let nodes_array = nodes.as_array().expect("Result should be a JSON array");
        assert!(!nodes_array.is_empty(), "Result array should not be empty");

      
        let found = nodes_array.iter().any(|node| node["uuid"].as_str() == Some(test_uuid));
        assert!(found, "Test node UUID should be present in the result");

        cleanup_test_data(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_get_newest_uuid() {
        let graph = get_graph().await;
        let test_uuid_old = "test-uuid-newest-old";
        let test_uuid_new = "test-uuid-newest-new";
        let test_color = "test-color-newest";
        let test_temp = 25556.1;
        let test_hum = 3000.6;
        let test_ts_old = "2100-10-08T00:00:00Z";
        let test_ts_new = "2100-10-08T01:00:00Z"; 
        let test_consume = 10000.6;
        let test_cost = 50000.6;

        assert!(setup_test_node(&graph, test_uuid_old, test_color, test_temp, test_hum, test_ts_old, test_consume, test_cost).await, "Setup failed for newest node test (old)");
     
        sleep(Duration::from_millis(10)).await;
        assert!(setup_test_node(&graph, test_uuid_new, test_color, test_temp, test_hum, test_ts_new, test_consume, test_cost).await, "Setup failed for newest node test (new)");

        let result = get_newest_uuid(&graph).await;
        assert!(result.is_some(), "get_newest_uuid should return Some(Value)");

        let uuids = result.unwrap();
        let uuids_array = uuids.as_array().expect("Result should be a JSON array");
        assert!(!uuids_array.is_empty(), "Result array should not be empty");

        
        assert_eq!(uuids_array[0].as_str(), Some(test_uuid_new), "The first UUID should be the newest one");

        cleanup_test_data(&graph, test_uuid_old, test_color, test_temp, test_hum, test_ts_old, test_consume, test_cost).await;
        cleanup_test_data(&graph, test_uuid_new, test_color, test_temp, test_hum, test_ts_new, test_consume, test_cost).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_get_temperature_humidity_at_time() {
        let graph = get_graph().await;
        let test_uuid = "test-uuid-temp-hum-time";
        let test_color = "test-color-temp-hum-time";
        let test_temp = 25.5;
        let test_hum = 60.1;
        let test_ts = "2100-10-09T12:30:00Z";
        let test_consume = 100.7;
        let test_cost = 50.7;

        assert!(setup_test_node(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await, "Setup failed for temp/hum at time test");

        let result = get_temperature_humidity_at_time(&graph, test_ts).await;
        assert!(result.is_some(), "Should find temp/hum for the given timestamp");

        let (temp, hum) = result.unwrap();
        assert_eq!(temp, test_temp, "Temperature should match");
        assert_eq!(hum, test_hum, "Humidity should match");

       
        let non_existent_ts = "1999-01-01T00:00:00Z";
        let result_none = get_temperature_humidity_at_time(&graph, non_existent_ts).await;
        assert!(result_none.is_none(), "Should return None for a non-existent timestamp");


        cleanup_test_data(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_get_nodes_in_time_range() {
        let graph = get_graph().await;
        let test_uuid1 = "test-uuid-timerange-1";
        let test_uuid2 = "test-uuid-timerange-2";
        let test_uuid_outside = "test-uuid-timerange-outside";
        let test_color = "test-color-timerange";
        let test_temp = 26.0;
        let test_hum = 61.0;
        let test_ts1 = "2100-11-01T10:00:00Z";
        let test_ts2 = "2100-11-01T11:00:00Z";
        let test_ts_outside = "2100-11-01T12:00:00Z";
        let test_consume = 101.0;
        let test_cost = 51.0;

        assert!(setup_test_node(&graph, test_uuid1, test_color, test_temp, test_hum, test_ts1, test_consume, test_cost).await, "Setup failed for time range test (1)");
        assert!(setup_test_node(&graph, test_uuid2, test_color, test_temp, test_hum, test_ts2, test_consume, test_cost).await, "Setup failed for time range test (2)");
        assert!(setup_test_node(&graph, test_uuid_outside, test_color, test_temp, test_hum, test_ts_outside, test_consume, test_cost).await, "Setup failed for time range test (outside)");

        let start_time = "2100-11-01T09:00:00Z";
        let end_time = "2100-11-01T11:30:00Z"; 

        let result = get_nodes_in_time_range(start_time, end_time, &graph).await;
        assert!(result.is_some(), "Should return Some for time range query");

        let nodes = result.unwrap();
        let nodes_array = nodes.as_array().expect("Result should be a JSON array");
        assert_eq!(nodes_array.len(), 2, "Should find exactly 2 nodes in the time range");

        let found1 = nodes_array.iter().any(|node| node["id"].as_str() == Some(test_uuid1));
        let found2 = nodes_array.iter().any(|node| node["id"].as_str() == Some(test_uuid2));
        assert!(found1, "Node 1 should be in the result");
        assert!(found2, "Node 2 should be in the result");

        cleanup_test_data(&graph, test_uuid1, test_color, test_temp, test_hum, test_ts1, test_consume, test_cost).await;
        cleanup_test_data(&graph, test_uuid2, test_color, test_temp, test_hum, test_ts2, test_consume, test_cost).await;
        cleanup_test_data(&graph, test_uuid_outside, test_color, test_temp, test_hum, test_ts_outside, test_consume, test_cost).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_get_nodes_with_temperature_or_humidity() {
        let graph = get_graph().await;
        let test_uuid = "test-uuid-temp-hum-val";
        let test_color = "test-color-temp-hum-val";
        let test_temp = 27.5;
        let test_hum = 65.5;
        let test_ts = "2100-11-02T00:00:00Z";
        let test_consume = 102.0;
        let test_cost = 52.0;

        assert!(setup_test_node(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await, "Setup failed for temp/hum value test");

        
        let result = get_nodes_with_temperature_or_humidity(test_temp, test_hum, &graph).await;
        assert!(result.is_some(), "Should return Some when searching by correct temp/hum");
        let nodes = result.unwrap();
        let nodes_array = nodes.as_array().expect("Result should be a JSON array");
        assert_eq!(nodes_array.len(), 1, "Should find exactly 1 node with the specified temp/hum");
        assert_eq!(nodes_array[0]["id"].as_str(), Some(test_uuid));

       
        let result_wrong = get_nodes_with_temperature_or_humidity(99.9, 99.9, &graph).await;
         assert!(result_wrong.is_some(), "Should return Some even if no nodes match");
         let nodes_wrong = result_wrong.unwrap();
         assert!(nodes_wrong.as_array().unwrap().is_empty(), "Should find 0 nodes with incorrect temp/hum");


        cleanup_test_data(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_get_nodes_with_energy_cost() {
        let graph = get_graph().await;
        let test_uuid = "test-uuid-cost-val";
        let test_color = "test-color-cost-val";
        let test_temp = 28.0;
        let test_hum = 68.0;
        let test_ts = "2100-11-03T00:00:00Z";
        let test_consume = 103.0;
        let test_cost = 53.5;

        assert!(setup_test_node(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await, "Setup failed for energy cost test");

        let result = get_nodes_with_energy_cost(test_cost, &graph).await;
        assert!(result.is_some(), "Should return Some when searching by correct cost");
        let nodes = result.unwrap();
        let nodes_array = nodes.as_array().expect("Result should be a JSON array");
        assert_eq!(nodes_array.len(), 1, "Should find exactly 1 node with the specified cost");
        assert_eq!(nodes_array[0]["id"].as_str(), Some(test_uuid));

      
        let result_wrong = get_nodes_with_energy_cost(999.99, &graph).await;
        assert!(result_wrong.is_some(), "Should return Some even if no nodes match");
        let nodes_wrong = result_wrong.unwrap();
        assert!(nodes_wrong.as_array().unwrap().is_empty(), "Should find 0 nodes with incorrect cost");

        cleanup_test_data(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_get_nodes_with_energy_consume() {
        let graph = get_graph().await;
        let test_uuid = "test-uuid-consume-val";
        let test_color = "test-color-consume-val";
        let test_temp = 29.0;
        let test_hum = 69.0;
        let test_ts = "2100-11-04T00:00:00Z";
        let test_consume = 104.5; 
        let test_cost = 54.0;

        assert!(setup_test_node(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await, "Setup failed for energy consume test");

        let result = get_nodes_with_energy_consume(test_consume, &graph).await;
        assert!(result.is_some(), "Should return Some when searching by correct consumption");
        let nodes = result.unwrap();
        let nodes_array = nodes.as_array().expect("Result should be a JSON array");
        assert_eq!(nodes_array.len(), 1, "Should find exactly 1 node with the specified consumption");
        assert_eq!(nodes_array[0]["id"].as_str(), Some(test_uuid));

      
        let result_wrong = get_nodes_with_energy_consume(9999.99, &graph).await;
        assert!(result_wrong.is_some(), "Should return Some even if no nodes match");
        let nodes_wrong = result_wrong.unwrap();
        assert!(nodes_wrong.as_array().unwrap().is_empty(), "Should find 0 nodes with incorrect consumption");

        cleanup_test_data(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await;
    }

    #[tokio::test]
    #[serial]
    async fn test_get_nodes_with_color() {
        let graph = get_graph().await;
        let test_uuid = "test-uuid-color-val";
        let test_color = "unique-test-color-blue"; 
        let test_temp = 30.0;
        let test_hum = 70.0;
        let test_ts = "2100-11-05T00:00:00Z";
        let test_consume = 105.0;
        let test_cost = 55.0;

        assert!(setup_test_node(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await, "Setup failed for color test");

        let result = get_nodes_with_color(test_color, &graph).await;
        assert!(result.is_some(), "Should return Some when searching by correct color");
        let nodes = result.unwrap();
        let nodes_array = nodes.as_array().expect("Result should be a JSON array");
        assert_eq!(nodes_array.len(), 1, "Should find exactly 1 node with the specified color");
        assert_eq!(nodes_array[0]["id"].as_str(), Some(test_uuid));

       
        let result_wrong = get_nodes_with_color("non-existent-color", &graph).await;
        assert!(result_wrong.is_some(), "Should return Some even if no nodes match");
        let nodes_wrong = result_wrong.unwrap();
        assert!(nodes_wrong.as_array().unwrap().is_empty(), "Should find 0 nodes with incorrect color");

        cleanup_test_data(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await;
    }

     #[tokio::test]
     #[serial]
     async fn test_process_large_json_file() {
         let graph = get_graph().await;
         let test_uuid = "test-uuid-bigfile";
         let test_color = "test-color-bigfile";
         let test_temp = 31.0;
         let test_hum = 71.0;
         let test_ts = "2100-11-06T00:00:00Z";
         let test_consume = 106.0;
         let test_cost = 56.0;

         let dummy_data = json!({
             "data": [{
                 "uuid": test_uuid,
                 "color": test_color,
                 "sensor_data": { "temperature": test_temp, "humidity": test_hum },
                 "timestamp": test_ts,
                 "energy_consume": test_consume,
                 "energy_cost": test_cost
             }]
         });
         
         fs::write("data.json", dummy_data.to_string()).expect("Failed to write dummy data.json");

         let result = process_large_json_file(&graph).await;

         fs::remove_file("data.json").expect("Failed to remove dummy data.json");

         assert!(result.is_ok(), "process_large_json_file should return Ok for valid dummy file. Got: {:?}", result.err());
         assert!(result.unwrap(), "process_large_json_file should return true indicating success");

       
         let node_check = get_specific_uuid_node(test_uuid, &graph).await;
         assert!(node_check.is_some(), "Node from dummy data.json should exist in the database");

         cleanup_test_data(&graph, test_uuid, test_color, test_temp, test_hum, test_ts, test_consume, test_cost).await;
     }

     #[tokio::test]
     #[serial]
     async fn test_process_large_json_file_empty_data() {
         let graph = get_graph().await;

     
         let dummy_data = json!({ "data": [] });
         fs::write("data.json", dummy_data.to_string()).expect("Failed to write empty dummy data.json");

         let result = process_large_json_file(&graph).await;

         fs::remove_file("data.json").expect("Failed to remove empty dummy data.json");

         
         assert!(result.is_ok(), "process_large_json_file should return Ok for empty data array. Got: {:?}", result.err());
         assert!(result.unwrap(), "process_large_json_file should return true for empty data array");
     }

     #[tokio::test]
     #[serial]
     async fn test_process_large_json_file_invalid_json() {
         let graph = get_graph().await;

      
         let invalid_json_content = r#"{"data": [ { "uuid": "test", "color": "red" },"#;
         fs::write("data.json", invalid_json_content).expect("Failed to write invalid dummy data.json");

         let result = process_large_json_file(&graph).await;

         fs::remove_file("data.json").expect("Failed to remove invalid dummy data.json");

         assert!(result.is_err(), "process_large_json_file should return Err for invalid JSON file");

         
         
     }

     #[tokio::test]
     #[serial]
     async fn test_process_large_json_file_missing_file() {
         let graph = get_graph().await;

         
         let _ = fs::remove_file("data.json");

         let result = process_large_json_file(&graph).await;
         assert!(result.is_err(), "process_large_json_file should return Err if data.json is not found");
         
     }

    // --- End Tests ---

    
}