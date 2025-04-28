use neo4rs::{Graph, query};
use log::{error, info, warn};
use serde_json::{Value, json};
use std::collections::HashMap;




async fn validate_new_item(item: &Value) -> bool {
    item.get("id").and_then(|v| v.as_f64().or_else(|| v.as_i64().map(|i| i as f64)).or_else(|| v.as_u64().map(|u| u as f64))).is_some()
        && item.get("uuid").and_then(|v| v.as_str()).is_some()
        && item.get("color").and_then(|v| v.as_str()).is_some()
        && item.get("sensor_data").map(|v| v.is_object()).unwrap_or(false)
        && item.get("sensor_data").and_then(|sd| sd.get("temperature")).and_then(|t| t.as_f64()).is_some()
        && item.get("sensor_data").and_then(|sd| sd.get("humidity")).and_then(|h| h.as_f64()).is_some()
        && item.get("timestamp").and_then(|v| v.as_str()).is_some()
        && item.get("energy_consume").and_then(|v| v.as_f64()).is_some()
        && item.get("energy_cost").and_then(|v| v.as_f64()).is_some()
}


async fn prepare_all_item_params(item: &Value) -> Option<HashMap<String, String>> {
    let mut params = HashMap::new();


    params.insert("uuid".to_string(), item.get("uuid")?.as_str()?.to_string());
    params.insert("color".to_string(), item.get("color")?.as_str()?.to_string());
    params.insert("temperature".to_string(), item.get("sensor_data")?.get("temperature")?.as_f64()?.to_string());
    params.insert("humidity".to_string(), item.get("sensor_data")?.get("humidity")?.as_f64()?.to_string());
    params.insert("timestamp".to_string(), item.get("timestamp")?.as_str()?.to_string());
    params.insert("energy_consume".to_string(), item.get("energy_consume")?.as_f64()?.to_string());
    params.insert("energy_cost".to_string(), item.get("energy_cost")?.as_f64()?.to_string());

    Some(params)
}

async fn validate_and_get_data_array(data: &Value) -> Result<&Vec<Value>, String> {
    match data.as_array() {
        Some(arr) => Ok(arr),
        None => Err("Input data is not a valid JSON array".to_string()),
    }
}


async fn acquire_global_id(graph: &Graph) -> Result<i64, String> {
    let cypher = "USE fabric.dbshard1
            MERGE (global_counter:GlobalIdCounter {name: 'global_counter'})
            ON CREATE SET global_counter.current = 0
            SET global_counter.current = global_counter.current + 1
            RETURN global_counter.current AS new_id";
    let query = query(cypher);
    match graph.execute(query).await {
        Ok(mut result) => {
            match result.next().await {
                Ok(Some(row)) => {
                    row.get::<i64>("new_id")
                       .map_err(|e| format!("Failed to extract new_id from row: {}", e))
                }
                Ok(None) => Err("Global ID counter query returned no rows.".to_string()),
                Err(e) => Err(format!("Failed to get next row from Global ID query result: {}", e)),
            }
        }
        Err(e) => Err(format!("Failed to execute Global ID query: {}", e)),
    }
}






pub async fn get_all_data(graph: &Graph) -> Result<Value, String> {
    let mut combined_results: HashMap<i64, Value> = HashMap::new();
   
    let mut shard2_data_map: HashMap<i64, Vec<Value>> = HashMap::new();
    
    let mut shard3_data_map: HashMap<i64, Vec<Value>> = HashMap::new();


  
    let shard1_cypher = r#"
        USE fabric.dbshard1
        MATCH (id_node:Id)
        OPTIONAL MATCH (id_node)-[:HAS_UUID]->(uuid_node:Uuid)
        OPTIONAL MATCH (id_node)-[:HAS_COLOR]->(color_node:Color)
        RETURN id_node.value AS id, uuid_node.value AS uuid, color_node.value AS color
    "#;
    let shard1_query = query(shard1_cypher);

    match graph.execute(shard1_query).await {
        Ok(mut result) => {
            while let Ok(Some(row)) = result.next().await {
                let id_val: i64 = match row.get("id") {
                    Ok(id) => id,
                    Err(e) => {
                        error!("Shard 1: Failed to get id from row: {}", e);
                        continue;
                    }
                };
                let uuid_val: Option<String> = row.get("uuid").ok();
                let color_val: Option<String> = row.get("color").ok();


            
                combined_results.insert(id_val, json!({
                    "id": id_val,
                    "uuid": uuid_val,
                    "color": color_val,
                    "sensor_data": [] 
                }));
            }
        }
        Err(e) => {
            let error_msg = format!("Failed to execute Shard 1 query in get_all_data: {}", e);
            error!("{}", error_msg);
            
        }
    }


   
    let shard2_cypher = r#"
        USE fabric.dbshard2
        MATCH (id_node:Id)-[:HAS_SENSOR_DATA]->(sensor_data_node:SensorData)
        OPTIONAL MATCH (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node:Temperature)
        OPTIONAL MATCH (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node:Humidity)
        RETURN id_node.value AS id, {
            temperature: temp_node.value,
            humidity: hum_node.value
        } AS sensor_reading

        
    "#;
    let shard2_query = query(shard2_cypher);

    match graph.execute(shard2_query).await {
        Ok(mut result) => {
            while let Ok(Some(row)) = result.next().await {
                let id_val: i64 = match row.get("id") {
                    Ok(id) => id,
                    Err(e) => {
                        error!("Shard 2: Failed to get id from row: {}", e);
                        continue;
                    }
                };

                let sensor_reading: Value = match row.get("sensor_reading") {
                    Ok(reading) => reading,
                    Err(e) => {
                        error!("Shard 2: Failed to get sensor_reading for id {}: {}", id_val, e);
                        continue;
                    }
                };


                shard2_data_map.entry(id_val).or_default().push(sensor_reading);
            }
        }
        Err(e) => {
            let error_msg = format!("Failed to execute Shard 2 query in get_all_data: {}", e);
            error!("{}", error_msg);


        }
    }


 
    let shard3_cypher = r#"
        USE fabric.dbshard3
        MATCH (id_node:Id) 
       
        OPTIONAL MATCH (id_node)-[:RECORDED_AT]->(time_node:Timestamp)
        OPTIONAL MATCH (id_node)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node:EnergyConsume)
        OPTIONAL MATCH (econsume_node)-[:HAS_ENERGY_COST]->(ecost_node:EnergyCost)

        RETURN id_node.value AS id, {
            timestamp: time_node.value,
            energy_consume: econsume_node.value,
            energy_cost: ecost_node.value
        } AS energy_reading

        ORDER BY id_node.value, time_node.value 
    "#;
    let shard3_query = query(shard3_cypher);

    match graph.execute(shard3_query).await {
        Ok(mut result) => {
            while let Ok(Some(row)) = result.next().await {
                 let id_val: i64 = match row.get("id") {
                    Ok(id) => id,
                    Err(e) => {
                        error!("Shard 3: Failed to get id from row: {}", e);
                        continue;
                    }
                };

                let energy_reading: Value = match row.get("energy_reading") {
                    Ok(reading) => reading,
                    Err(e) => {
                        error!("Shard 3: Failed to get energy_reading for id {}: {}", id_val, e);
                        continue;
                    }
                };
                
                shard3_data_map.entry(id_val).or_default().push(energy_reading);
            }
        }
        Err(e) => {
            let error_msg = format!("Failed to execute Shard 3 query in get_all_data: {}", e);
            error!("{}", error_msg);


        }
    }


    for (id, base_data) in combined_results.iter_mut() {
        if let Some(obj) = base_data.as_object_mut() {

            let mut merged_sensor_data: Vec<Value> = Vec::new();


            let s2_readings = shard2_data_map.get(id).cloned().unwrap_or_default();
            let s3_readings = shard3_data_map.get(id).cloned().unwrap_or_default();


         
            let num_readings = s2_readings.len().max(s3_readings.len());

            for i in 0..num_readings {
                let mut combined_reading = serde_json::Map::new();

               
                if let Some(s2_val) = s2_readings.get(i) {
                    if let Some(s2_obj) = s2_val.as_object() {
                        if let Some(temp) = s2_obj.get("temperature") { combined_reading.insert("temperature".to_string(), temp.clone()); }
                        if let Some(hum) = s2_obj.get("humidity") { combined_reading.insert("humidity".to_string(), hum.clone()); }
                    }
                }

           
                if let Some(s3_val) = s3_readings.get(i) {
                     if let Some(s3_obj) = s3_val.as_object() {
                        if let Some(ts) = s3_obj.get("timestamp") { combined_reading.insert("timestamp".to_string(), ts.clone()); }
                        if let Some(econ) = s3_obj.get("energy_consume") { combined_reading.insert("energy_consume".to_string(), econ.clone()); }
                        if let Some(ecost) = s3_obj.get("energy_cost") { combined_reading.insert("energy_cost".to_string(), ecost.clone()); }
                    }
                }

                if !combined_reading.is_empty() {
                    merged_sensor_data.push(Value::Object(combined_reading));
                }
            }


         
            let valid_readings: Vec<Value> = merged_sensor_data.into_iter()
                .filter(|reading| !reading.is_null() && reading.is_object() && !reading.as_object().unwrap().is_empty())
                .collect();
            obj.insert("sensor_data".to_string(), json!(valid_readings));
        }

    }


    let final_data: Vec<Value> = combined_results.into_values().collect();
    info!("Retrieved and combined data from 3 shards for {} entries.", final_data.len());
    Ok(json!(final_data))
}




pub async fn get_data_by_id(id: i64, graph: &Graph) -> Result<Value, String> {
    let params = HashMap::from([("target_id".to_string(), id)]);


   
    let shard1_cypher = r#"
        USE fabric.dbshard1
        MATCH (id_node:Id {value: $target_id})
        OPTIONAL MATCH (id_node)-[:HAS_UUID]->(uuid_node:Uuid)
        OPTIONAL MATCH (id_node)-[:HAS_COLOR]->(color_node:Color)
        RETURN id_node.value AS id, uuid_node.value AS uuid, color_node.value AS color
        LIMIT 1
    "#;

    let shard1_query = query(shard1_cypher).params(params.clone());
    info!("Executing Shard 1 query for ID {}", id);
    let (id_val, uuid_val, color_val) = match graph.execute(shard1_query).await {
        Ok(mut result) => {
            match result.next().await {
                Ok(Some(row)) => {
                    let id_res: i64 = row.get("id").map_err(|e| format!("Shard 1: Failed to get id: {}", e))?;
                    if id_res != id {
                         return Err(format!("Shard 1: ID mismatch, expected {}, got {}", id, id_res));
                    }
                    let uuid_res: Option<String> = row.get("uuid").ok();
                    let color_res: Option<String> = row.get("color").ok();
                    (id_res, uuid_res, color_res)
                }
                Ok(None) => return Err(format!("No data found for ID {} in Shard 1", id)),
                Err(e) => return Err(format!("Shard 1: Failed to process result row for ID {}: {}", id, e)),
            }
        }
        Err(e) => return Err(format!("Failed to execute Shard 1 query for ID {}: {}", id, e)),
    };


    let shard2_cypher = r#"
        USE fabric.dbshard2
        MATCH (id_node_s2:Id {value: $target_id})
        OPTIONAL MATCH (id_node_s2)-[:HAS_SENSOR_DATA]->(sensor_data_node:SensorData)
        OPTIONAL MATCH (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node:Temperature)
        OPTIONAL MATCH (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node:Humidity)
       
        WITH sensor_data_node, temp_node, hum_node
        WHERE sensor_data_node IS NOT NULL
        RETURN {
            temperature: temp_node.value,
            humidity: hum_node.value
        } AS sensor_reading
        
    "#;
    let shard2_query = query(shard2_cypher).params(params.clone()); 
    info!("Executing Shard 2 query for ID {}", id);
    let mut shard2_readings_list: Vec<Value> = Vec::new();

    match graph.execute(shard2_query).await {
        Ok(mut result) => {
            while let Ok(Some(row)) = result.next().await {
                 match row.get::<Value>("sensor_reading") {
                    Ok(reading) => {
                        if !reading.is_null() && reading.is_object() {
                             shard2_readings_list.push(reading);
                        } else {
                             warn!("Shard 2: Got null or non-object sensor reading for ID {}", id);
                        }
                    },
                    Err(e) => {
                        error!("Shard 2: Failed to get sensor_reading from row for ID {}: {}", id, e);
                    }
                }
            }

        }
        Err(e) => {
            warn!("Shard 2 query execution failed or returned no data for ID {} (may indicate ID not present or other issue: {}). Proceeding with potentially incomplete sensor data.", id, e);

        }
    };


 
    let shard3_cypher = r#"
        USE fabric.dbshard3
        MATCH (id_node_s3:Id {value: $target_id})
        OPTIONAL MATCH (id_node_s3)-[:RECORDED_AT]->(time_node:Timestamp)
        OPTIONAL MATCH (id_node_s3)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node:EnergyConsume)
        OPTIONAL MATCH (econsume_node)-[:HAS_ENERGY_COST]->(ecost_node:EnergyCost)

        WITH time_node, econsume_node, ecost_node 
        WHERE time_node IS NOT NULL OR econsume_node IS NOT NULL 
        RETURN {
            timestamp: time_node.value,
            energy_consume: econsume_node.value,
            energy_cost: ecost_node.value
        } AS energy_reading
        ORDER BY time_node.value 
    "#;

    let shard3_query = query(shard3_cypher).params(params); 
    info!("Executing Shard 3 query for ID {}", id);
    let mut shard3_readings_list: Vec<Value> = Vec::new();

     match graph.execute(shard3_query).await {
        Ok(mut result) => {
            while let Ok(Some(row)) = result.next().await {
                 match row.get::<Value>("energy_reading") {
                    Ok(reading) => {
                        if !reading.is_null() && reading.is_object() {
                             shard3_readings_list.push(reading);
                        } else {
                             warn!("Shard 3: Got null or non-object energy reading for ID {}", id);
                        }
                    },
                    Err(e) => {
                        error!("Shard 3: Failed to get energy_reading from row for ID {}: {}", id, e);
                    }
                }
            }

        }
        Err(e) => {
             warn!("Shard 3 query execution failed or returned no data for ID {} (may indicate ID not present or other issue: {}). Proceeding with potentially incomplete sensor data.", id, e);

        }
    };



    let mut merged_sensor_data: Vec<Value> = Vec::new();
    let num_readings = shard2_readings_list.len().max(shard3_readings_list.len());

    for i in 0..num_readings {
        let mut combined_reading = serde_json::Map::new();


        if let Some(s2_val) = shard2_readings_list.get(i) {
            if let Some(s2_obj) = s2_val.as_object() {
                if let Some(temp) = s2_obj.get("temperature") { combined_reading.insert("temperature".to_string(), temp.clone()); }
                if let Some(hum) = s2_obj.get("humidity") { combined_reading.insert("humidity".to_string(), hum.clone()); }
            }
        }

        if let Some(s3_val) = shard3_readings_list.get(i) {
             if let Some(s3_obj) = s3_val.as_object() {
                if let Some(ts) = s3_obj.get("timestamp") { combined_reading.insert("timestamp".to_string(), ts.clone()); }
                if let Some(econ) = s3_obj.get("energy_consume") { combined_reading.insert("energy_consume".to_string(), econ.clone()); }
                if let Some(ecost) = s3_obj.get("energy_cost") { combined_reading.insert("energy_cost".to_string(), ecost.clone()); }
            }
        }

        if !combined_reading.is_empty() {
            merged_sensor_data.push(Value::Object(combined_reading));
        }
    }

     let valid_readings: Vec<Value> = merged_sensor_data.into_iter()
        .filter(|reading| !reading.is_null() && reading.is_object() && !reading.as_object().unwrap().is_empty())
        .collect();


    let combined_data = json!({
        "id": id_val,
        "uuid": uuid_val,
        "color": color_val,
        "sensor_data": valid_readings 
    });
    info!("Successfully retrieved and combined data from 3 shards for ID {}: {:?}", id, combined_data);
    Ok(combined_data)
}


pub async fn create_new_nodes(data: &Value, graph: &Graph) -> Result<usize, String> {

    let data_array = match validate_and_get_data_array(data).await {
        Ok(arr) => arr,
        Err(e) => return Err(format!("Input validation failed: {}", e)),
    };

    if data_array.is_empty() {
        info!("Received empty validated data array. No nodes will be created.");
        return Ok(0);
    }


    for (index, item) in data_array.iter().enumerate() {
        if !validate_new_item(item).await {
            let error_msg = format!("Invalid item structure at index {}: {:?}", index, item);
            error!("{}", error_msg);
            return Err(error_msg);
        }
    }

    let mut processed_count = 0;
    let mut errors = Vec::new();


    for (index, item) in data_array.iter().enumerate() {

        let new_id = match acquire_global_id(graph).await {
            Ok(id) => id,
            Err(e) => {
                let error_msg = format!("Failed to acquire global ID for item at index {}: {}", index, e);
                error!("{}", error_msg);
                errors.push(error_msg);
                continue;
            }
        };

        let params = match prepare_all_item_params(item).await {
             Some(p) => p,
             None => {
                 let error_msg = format!("Failed to extract parameters for item at index {}: {:?}", index, item);
                 error!("{}", error_msg);
                 errors.push(error_msg);
                 continue;
             }
         };

        let mut params_with_id = params; 
        params_with_id.insert("new_id".to_string(), new_id.to_string());

     
        let graph_ref1 = graph.clone(); 
        let graph_ref2 = graph.clone();
        let graph_ref3 = graph.clone();
        let params_ref1 = params_with_id.clone(); 
        let params_ref2 = params_with_id.clone();
        let params_ref3 = params_with_id.clone();


        let shard1_handle = tokio::spawn(async move { execute_shard1_query(&graph_ref1, &params_ref1).await });
        let shard2_handle = tokio::spawn(async move { execute_shard2_query(&graph_ref2, &params_ref2).await });
        let shard3_handle = tokio::spawn(async move { execute_shard3_query(&graph_ref3, &params_ref3).await });

        
        let (res1, res2, res3) = tokio::join!(shard1_handle, shard2_handle, shard3_handle);

        let shard1_ok = match res1 {
            Ok(Ok(_)) => { info!("Shard 1 successful for ID {}", new_id); true },
            Ok(Err(e)) => { error!("Shard 1 failed for ID {}: {}", new_id, e); errors.push(format!("Shard 1 failed for ID {}: {}", new_id, e)); false },
            Err(e) => { error!("Shard 1 task panicked/cancelled for ID {}: {}", new_id, e); errors.push(format!("Shard 1 task failed (join) for ID {}: {}", new_id, e)); false },
        };
        let shard2_ok = match res2 {
            Ok(Ok(_)) => { info!("Shard 2 successful for ID {}", new_id); true },
            Ok(Err(e)) => { error!("Shard 2 failed for ID {}: {}", new_id, e); errors.push(format!("Shard 2 failed for ID {}: {}", new_id, e)); false },
            Err(e) => { error!("Shard 2 task panicked/cancelled for ID {}: {}", new_id, e); errors.push(format!("Shard 2 task failed (join) for ID {}: {}", new_id, e)); false },
        };
        let shard3_ok = match res3 {
            Ok(Ok(_)) => { info!("Shard 3 successful for ID {}", new_id); true },
            Ok(Err(e)) => { error!("Shard 3 failed for ID {}: {}", new_id, e); errors.push(format!("Shard 3 failed for ID {}: {}", new_id, e)); false },
            Err(e) => { error!("Shard 3 task panicked/cancelled for ID {}: {}", new_id, e); errors.push(format!("Shard 3 task failed (join) for ID {}: {}", new_id, e)); false },
        };

        if shard1_ok && shard2_ok && shard3_ok {
            processed_count += 1;
        } else {
           
            warn!("At least one shard failed for item at index {} (ID {}). Data might be inconsistent.", index, new_id);
           
        }

    }


    if errors.is_empty() {
        info!(
            "Successfully processed {} out of {} items across both shards.",
            processed_count,
            data_array.len()
        );
        Ok(processed_count)
    } else {

        let combined_error = format!(
            "Successfully processed {} out of {} items. Encountered {} errors: {}",
            processed_count,
            data_array.len(),
            errors.len(),
            errors.join("; ")
        );
        error!("{}", combined_error);


        Ok(processed_count)
    }
}



async fn execute_shard3_query(graph: &Graph, params: &HashMap<String, String>) -> Result<(), String> {
    let cypher = r#"
        USE fabric.dbshard3 

        MERGE (id_node:Id {value: toInteger($new_id)})


        CREATE (time_node:Timestamp {value: $timestamp})
        CREATE (econsume_node:EnergyConsume {value: toFloat($energy_consume)})
        CREATE (ecost_node:EnergyCost {value: toFloat($energy_cost)})

        MERGE (id_node)-[:RECORDED_AT]->(time_node)
        MERGE (id_node)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node)
        MERGE (econsume_node)-[:HAS_ENERGY_COST]->(ecost_node)

        RETURN id_node.value AS processed_id
    "#;
    let query = query(cypher).params(params.clone());
     match graph.execute(query).await {
        Ok(mut result) => {
            match result.next().await {
                Ok(Some(_row)) => Ok(()),
                Ok(None) => Err("Shard 3 query executed but returned no confirmation row.".to_string()),
                Err(e) => Err(format!("Failed to process result row for Shard 3 query: {}", e)),
            }
        }
        Err(e) => Err(format!("Failed to execute Shard 3 query: {}", e)),
    }
}


async fn execute_shard1_query(graph: &Graph, params: &HashMap<String, String>) -> Result<(), String> {
    let cypher = r#"
        USE fabric.dbshard1

        CREATE (id_node:Id {value: toInteger($new_id)})
        CREATE (uuid_node:Uuid {value: $uuid})

        MERGE (color_node:Color {value: $color})

        MERGE (id_node)-[:HAS_UUID]->(uuid_node)
        MERGE (id_node)-[:HAS_COLOR]->(color_node)
        RETURN id_node.value AS processed_id
    "#;
    let query = query(cypher).params(params.clone());
    match graph.execute(query).await {
        Ok(mut result) => {
            match result.next().await {
                Ok(Some(_row)) => Ok(()),
                Ok(None) => Err("Shard 1 query executed but returned no confirmation row.".to_string()),
                Err(e) => Err(format!("Failed to process result row for Shard 1 query: {}", e)),
            }
        }
        Err(e) => Err(format!("Failed to execute Shard 1 query: {}", e)),
    }
}


async fn execute_shard2_query(graph: &Graph, params: &HashMap<String, String>) -> Result<(), String> {
    let cypher = r#"
        USE fabric.dbshard2

        MERGE (id_node:Id {value: toInteger($new_id)})

        CREATE (sensor_data_node:SensorData) 

        MERGE (temp_node:Temperature {value: toFloat($temperature)})
        MERGE (hum_node:Humidity {value: toFloat($humidity)})

        MERGE (id_node)-[:HAS_SENSOR_DATA]->(sensor_data_node)
        MERGE (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node)
        MERGE (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node)


        RETURN id_node.value AS processed_id
    "#;
    let query = query(cypher).params(params.clone());
     match graph.execute(query).await {
        Ok(mut result) => {
            match result.next().await {
                Ok(Some(_row)) => Ok(()),
                Ok(None) => Err("Shard 2 query executed but returned no confirmation row.".to_string()),
                Err(e) => Err(format!("Failed to process result row for Shard 2 query: {}", e)),
            }
        }
        Err(e) => Err(format!("Failed to execute Shard 2 query: {}", e)),
    }
}
