#[cfg(test)]
mod tests {
    use std::sync::Arc;

    use neo4rs::{query, Graph};
    use serde_json::json;
    use crate::db;
    use std::fs::OpenOptions;
    use std::io::Write;
    use std::fs;

    use crate::db_operations::crud::{get_specific_uuid_node,create_new_relation, get_paginated_uuids};
    use crate::db_operations::relationshipexport::export_all_with_relationships;
   

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
        db_handler.get_primary_db().await
    }

    #[tokio::test]
    async fn test_empty_data() {
        let graph = get_graph().await;
        let data = json!({ "data": [] });
        
        let result = create_new_relation(&data, &graph).await;
        
        assert!(matches!(result, Ok(false)), "Should return Ok(false) for empty array");
    }

    #[tokio::test]
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
        // false
        let result = create_new_relation(&data, &graph).await;
        assert!(result.is_err(), "Should return Err for invalid data");
    }

    #[tokio::test]
    async fn test_valid_data() {
        let graph = get_graph().await;
        let test_uuid = "test-uuid-validate";
        
       
        let data = json!({
            "data": [{
                "uuid": test_uuid,
                "color": "test-color",
                "sensor_data": {
                    "temperature": 25555.5,
                    "humidity": 3000.0  
                },
                "timestamp": "2100-10-01T00:00:00Z",
                "energy_consume": 10000.0,
                "energy_cost": 50000.0
            }]
        });
        // true
        let result = create_new_relation(&data, &graph).await;
        assert!(matches!(result, Ok(true)), "Should return Ok(true) for valid data");

        cleanup_test_data(&graph, test_uuid).await;
    }

    #[tokio::test]
    async fn test_duplicate_uuid() {
        let graph = get_graph().await;
        let test_uuid = "test-uuid-duplicate";
        
        
        let data = json!({
            "data": [{
                "uuid": test_uuid,
                "color": "test-color",
                "sensor_data": {
                    "temperature": 25555.5,
                    "humidity": 3000.0 
                },
                "timestamp": "2023-10-01T00:00:00Z",
                "energy_consume": 10000.0,
                "energy_cost": 50000.0
            }]
        });
        // true
        let first_result = create_new_relation(&data, &graph).await;
        assert!(matches!(first_result, Ok(true)), "First insertion should return Ok(true)");
        
        // false
        let second_result = create_new_relation(&data, &graph).await;
        assert!(matches!(second_result, Ok(false)), "Second insertion should return Ok(false)");

        cleanup_test_data(&graph, test_uuid).await;
    }

    #[tokio::test]
    async fn test_serialization_error() {
        let graph = get_graph().await;
        
       
        let data = json!({
            "data": [{
                "uuid": "test-uuid",
                "color": "test-color",
               
                "sensor_data": {
                    "temperature": f64::NAN,  
                    "humidity": 30.0
                },
                "timestamp": "2023-10-01T00:00:00Z",
                "energy_consume": 100.0,
                "energy_cost": 50.0
            }]
        });
        // error
        let result = create_new_relation(&data, &graph).await;

        let iserror = result.is_err();

        write_to_log(&format!(
            "Test for serialization error returned: {:?}, success: {:?}",
             result, iserror
        ))
        .await;
        assert!(iserror, "Should return Err for serialization error");
    }

    #[tokio::test]
    async fn test_export_all_with_relationships() {
        let graph = get_graph().await;
        
        let result = export_all_with_relationships(&graph, Some(100)).await;
        
    
        assert!(result.is_some(), "Exportfunktion sollte Some(Value) zurückgeben");

        let json_result = result.unwrap();
        
    
        let output = json_result.to_string();
        fs::write("export_all_data.json", &output).expect("Fehler beim Schreiben der JSON-Datei");
        assert!(!output.is_empty(), "Exportierte Datei sollte nicht leer sein");

        
    }

    #[tokio::test]
    async fn test_get_specific_uuid_node() {
        let graph = get_graph().await;
        let test_uuid = "test-uuid-specific";
    
        let data = json!({
            "data": [{
                "uuid": test_uuid,
                "color": "test-color",
                "sensor_data": {
                    "temperature": 25555.5,
                    "humidity": 3000.0
                },
                "timestamp": "2023-10-01T00:00:00Z",
                "energy_consume": 10000.0,
                "energy_cost": 50000.0
            }]
        });
    
        let _ = create_new_relation(&data, &graph).await;
        let start_time = std::time::Instant::now();
        
        let result = get_specific_uuid_node(test_uuid, &graph).await;
        let elapsed = start_time.elapsed();
        
        let test_succeeded = result.is_some();
        
        write_to_log(&format!(
            "Test for getting a node with uuid: execution time: {:?}, returned: {:?}, success: {}",
            elapsed, result, test_succeeded
        ))
        .await;
    
        assert!(test_succeeded, "Should return Some(Value) for specific UUID");
    
        cleanup_test_data(&graph, test_uuid).await;
    }
    
    #[tokio::test]
    async fn test_get_paginated_uuids() {
        let graph = get_graph().await;
        
      
        let first_page_result = get_paginated_uuids(&graph, 0).await;
        assert!(first_page_result.is_some(), "Should return Some(Value) for first page");
        
        let first_page = first_page_result.unwrap();
        let uuids = first_page["uuids"].as_array().unwrap();
        let total_count = first_page["pagination"]["total_count"].as_u64().unwrap() as usize;
        let total_pages = first_page["pagination"]["total_pages"].as_u64().unwrap() as usize;
        let current_page = first_page["pagination"]["current_page"].as_u64().unwrap() as usize;
        let page_size = first_page["pagination"]["page_size"].as_u64().unwrap() as usize;
        
        assert_eq!(current_page, 0, "Current page should be 0");
        assert_eq!(page_size, 50, "Page size should be 50");
        
       
        write_to_log(&format!(
            "Pagination test - Total count: {}, Total pages: {}, First page UUIDs: {}",
            total_count, total_pages, uuids.len()
        )).await;
        
        
        let expected_first_page_count = std::cmp::min(page_size, total_count);
        assert_eq!(uuids.len(), expected_first_page_count, 
                  "First page should contain the expected number of UUIDs");
        
       
        if total_pages > 1 {
            let last_page_index = total_pages - 1;
            let last_page_result = get_paginated_uuids(&graph, last_page_index).await;
            assert!(last_page_result.is_some(), "Should return Some(Value) for last page");
            
            let last_page = last_page_result.unwrap();
            let last_page_uuids = last_page["uuids"].as_array().unwrap();
            let last_page_current = last_page["pagination"]["current_page"].as_u64().unwrap() as usize;
            
            assert_eq!(last_page_current, last_page_index, "Current page should be the last page index");
            
        
            write_to_log(&format!(
                "Pagination test - Last page ({}): UUIDs count: {}",
                last_page_index, last_page_uuids.len()
            )).await;
          
            let expected_last_page_count = if total_count % page_size == 0 {
                page_size
            } else {
                total_count % page_size
            };
            
            assert_eq!(last_page_uuids.len(), expected_last_page_count,
                      "Last page should contain the expected number of UUIDs");
        }
    }
    





    async fn cleanup_test_data(graph: &Graph, uuid: &str) {
        let q = query("MATCH (u:UUID {id: $uuid}) DETACH DELETE u")
            .param("uuid", uuid);
        let _ = graph.run(q).await;
 
        let q = query("MATCH (c:Color {value: $value}) DETACH DELETE c")
            .param("value", "test-color");
        let _ = graph.run(q).await;

        let q = query("MATCH (t:Temperature {value: $value}) DETACH DELETE t")
            .param("value", 25555.5);
        let _ = graph.run(q).await;
    
        let q = query("MATCH (h:Humidity {value: $value}) DETACH DELETE h")
            .param("value", 3000.0);
        let _ = graph.run(q).await;
    
        let q = query("MATCH (ts:Timestamp {value: $value}) DETACH DELETE ts")
            .param("value", "2023-10-01T00:00:00Z");
        let _ = graph.run(q).await;
        
        let q = query("MATCH (ts:Timestamp {value: $value}) DETACH DELETE ts")
            .param("value", "2100-10-01T00:00:00Z");
        let _ = graph.run(q).await;
    
        let q = query("MATCH (ec:EnergyCost {value: $value}) DETACH DELETE ec")
            .param("value", 50000.0);
        let _ = graph.run(q).await;
    
        let q = query("MATCH (eco:EnergyConsume {value: $value}) DETACH DELETE eco")
            .param("value", 10000.0);
        let _ = graph.run(q).await;
    }
}