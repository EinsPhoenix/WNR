use neo4rs::{Graph, query};
use log::{error, info, warn};
use serde_json::{Value, json};
use std::collections::HashMap;
use super::cypher_queries::*;

// Retrieves and combines data from multiple database shards.
// Input: &Graph - a reference to the Neo4j graph instance.
// Returns: Result<Value, String> - combined data as JSON or an error message.
pub async fn get_all_data(graph: &Graph) -> Result<Value, String> {
    let mut combined_results: HashMap<i64, Value> = HashMap::new();
   
    let mut shard2_data_map: HashMap<i64, Vec<Value>> = HashMap::new();
    
    let mut shard3_data_map: HashMap<i64, Vec<Value>> = HashMap::new();

    let shard1_cypher = GET_ALL_DATA_SHARD1;
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

    let shard2_cypher = GET_ALL_DATA_SHARD2;
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

    let shard3_cypher = GET_ALL_DATA_SHARD3;
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

// Deletes data for a list of IDs from multiple database shards.
// Input: ids_to_delete - a vector of IDs to delete, &Graph - a reference to the Neo4j graph instance.
// Returns: Result<usize, String> - the number of successfully deleted nodes or an error message.
pub async fn delete_data_by_id(ids_to_delete: &Vec<i64>, graph: &Graph) -> Result<usize, String> {
    let mut deleted_count = 0;
    
    for &id in ids_to_delete {
        let params = HashMap::from([("target_id".to_string(), id)]);

        let shard1_cypher = DELETE_DATA_BY_ID_SHARD1;
        let shard1_query = query(shard1_cypher).params(params.clone());

        let shard2_cypher = DELETE_DATA_BY_ID_SHARD2;
        let shard2_query = query(shard2_cypher).params(params.clone());
        
        let shard3_cypher = DELETE_DATA_BY_ID_SHARD3;
        let shard3_query = query(shard3_cypher).params(params.clone()); 

        let mut node_existed = false;
        
        let (shard1_result, shard2_result, shard3_result) = tokio::join!(
            graph.execute(shard1_query),
            graph.execute(shard2_query),
            graph.execute(shard3_query)
        );

        match shard1_result {
            Ok(mut result) => {
                if let Ok(Some(row)) = result.next().await {
                    if row.get::<i64>("deleted_id").is_ok() {
                        node_existed = true;
                        info!("Successfully deleted data from Shard 1 for ID {}", id);
                    }
                }
            },
            Err(e) => {
                warn!("Failed to delete data from Shard 1 for ID {}: {}", id, e);
            }
        }

        match shard2_result {
            Ok(_) => {
                info!("Successfully deleted data from Shard 2 for ID {}", id);
            },
            Err(e) => {
                warn!("Failed to delete data from Shard 2 for ID {}: {}", id, e);
            }
        }

        match shard3_result {
            Ok(_) => {
                info!("Successfully deleted data from Shard 3 for ID {}", id);
            },
            Err(e) => {
                warn!("Failed to delete data from Shard 3 for ID {}: {}", id, e);
            }
        }

        if node_existed {
            deleted_count += 1;
        }
    }

    info!("Successfully deleted {} nodes in total", deleted_count);
    Ok(deleted_count)
}

// Retrieves data for a specific ID from multiple database shards.
// Input: id - the target ID, &Graph - a reference to the Neo4j graph instance.
// Returns: Result<Value, String> - combined data for the ID as JSON or an error message.
pub async fn get_data_by_id(id: i64, graph: &Graph) -> Result<Value, String> {
    let params = HashMap::from([("target_id".to_string(), id)]);

    let shard1_cypher = GET_DATA_BY_ID_SHARD1;

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

    let shard2_cypher = GET_DATA_BY_ID_SHARD2;
    let shard2_query_fut = graph.execute(query(shard2_cypher).params(params.clone())); 
    
    let shard3_cypher = GET_DATA_BY_ID_SHARD3;
    let shard3_query_fut = graph.execute(query(shard3_cypher).params(params.clone())); 

    info!("Executing Shard 2 and Shard 3 queries concurrently for ID {}", id);
    let (shard2_execution_result, shard3_execution_result) = tokio::join!(shard2_query_fut, shard3_query_fut);

    let mut shard2_readings_list: Vec<Value> = Vec::new();
    match shard2_execution_result {
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

    let mut shard3_readings_list: Vec<Value> = Vec::new();
     match shard3_execution_result {
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

// Retrieves the newest IDs from the database.
// Input: &Graph - a reference to the Neo4j graph instance.
// Returns: Result<Value, String> - newest IDs as JSON or an error message.
pub async fn get_newest_ids(graph: &Graph) -> Result<Value, String> {
    let mut ordered_newest_events_s3: Vec<(i64, Value)> = Vec::new();
    let mut distinct_ids_from_s3_events: std::collections::HashSet<i64> = std::collections::HashSet::new();

    let s3_newest_cypher = GET_NEWEST_ENERGYDATA;
    let s3_newest_query = query(s3_newest_cypher);

    info!("Executing GET_NEWEST_ENERGYDATA query on Shard 3");
    match graph.execute(s3_newest_query).await {
        Ok(mut result) => {
            while let Ok(Some(row)) = result.next().await {
                match row.get::<i64>("id") {
                    Ok(id_val) => {
                        match row.get::<Value>("energy_reading") {
                            Ok(energy_reading_val) => {
                                ordered_newest_events_s3.push((id_val, energy_reading_val));
                                distinct_ids_from_s3_events.insert(id_val);
                            }
                            Err(e) => {
                                error!("Shard 3 newest: Failed to get energy_reading for id {}: {}", id_val, e);
                            }
                        }
                    }
                    Err(_) => {
                        warn!("Shard 3 newest: Encountered an entry with missing or invalid ID. Skipping.");
                    }
                }
            }
        }
        Err(e) => {
            let error_msg = format!("Failed to execute GET_NEWEST_ENERGYDATA query: {}", e);
            error!("{}", error_msg);
            return Err(error_msg);
        }
    }

    if ordered_newest_events_s3.is_empty() {
        info!("No newest data found in Shard 3 to determine order.");
        return Ok(json!([]));
    }

    let target_ids_vec: Vec<i64> = distinct_ids_from_s3_events.into_iter().collect();
    let has_target_ids = !target_ids_vec.is_empty();
    let params_for_ids = HashMap::from([("target_ids".to_string(), target_ids_vec.clone())]);


    let mut s1_meta_map: HashMap<i64, (Option<String>, Option<String>)> = HashMap::new();
    if has_target_ids {
        let s1_data_cypher = GET_DATA_BY_IDS_SHARD1;
        let s1_data_query = query(s1_data_cypher).params(params_for_ids.clone());

       
        match graph.execute(s1_data_query).await {
            Ok(mut result) => {
                while let Ok(Some(row)) = result.next().await {
                    if let Ok(id_val) = row.get::<i64>("id") {
                        let uuid_val: Option<String> = row.get("uuid").ok();
                        let color_val: Option<String> = row.get("color").ok();
                        s1_meta_map.insert(id_val, (uuid_val, color_val));
                    }
                }
            }
            Err(e) => {
                warn!("Failed to execute Shard 1 data query for newest IDs: {}. Data from Shard 1 might be missing.", e);
            }
        }
    }

    let mut s2_sensor_map: HashMap<i64, Vec<Value>> = HashMap::new();
    
    if !target_ids_vec.is_empty() {
        let s2_data_cypher = GET_DATA_BY_IDS_SHARD2;
        let s2_data_query = query(s2_data_cypher).params(params_for_ids.clone());

        info!("Executing GET_DATA_BY_IDS_SHARD2 for {} distinct IDs", target_ids_vec.len());
        match graph.execute(s2_data_query).await {
            Ok(mut result) => {
                while let Ok(Some(row)) = result.next().await {
                    if let Ok(id_val) = row.get::<i64>("id") {
                        if let Ok(sensor_reading) = row.get::<Value>("sensor_reading") {
                            if !sensor_reading.is_null() && sensor_reading.is_object() {
                                 s2_sensor_map.entry(id_val).or_default().push(sensor_reading);
                            }
                        }
                    }
                }
            }
            Err(e) => {
                warn!("Failed to execute Shard 2 data query for newest IDs: {}. Sensor data from Shard 2 might be missing.", e);
            }
        }
    }

    let mut s3_energy_map: HashMap<i64, Vec<Value>> = HashMap::new();
    
    if !target_ids_vec.is_empty() {
        let s3_data_cypher = GET_ENERGY_DATA_BY_IDS_SHARD3;
        let s3_data_query = query(s3_data_cypher).params(params_for_ids.clone());

        info!("Executing GET_ENERGY_DATA_BY_IDS_SHARD3 for {} distinct IDs", target_ids_vec.len());
        match graph.execute(s3_data_query).await {
            Ok(mut result) => {
                while let Ok(Some(row)) = result.next().await {
                    if let Ok(id_val) = row.get::<i64>("id") {
                        if let Ok(energy_reading) = row.get::<Value>("energy_reading") {
                             if !energy_reading.is_null() && energy_reading.is_object() {
                                s3_energy_map.entry(id_val).or_default().push(energy_reading);
                             }
                        }
                    }
                }
            }
            Err(e) => {
                warn!("Failed to execute Shard 3 data query for newest IDs: {}. Energy data from Shard 3 might be incomplete.", e);
            }
        }
    }

    let mut final_results: Vec<Value> = Vec::new();
    for (id_of_event, _specific_s3_event_data) in ordered_newest_events_s3 {
        let (uuid_val, color_val) = s1_meta_map.get(&id_of_event)
            .cloned()
            .unwrap_or((None, None));

        let s2_readings_for_id = s2_sensor_map.get(&id_of_event).cloned().unwrap_or_default();
        let s3_readings_for_id = s3_energy_map.get(&id_of_event).cloned().unwrap_or_default();

  
        let mut merged_sensor_data_list: Vec<Value> = Vec::new();
        let num_readings_to_merge = s2_readings_for_id.len().max(s3_readings_for_id.len());

        for i in 0..num_readings_to_merge {
            let mut combined_reading_map = serde_json::Map::new();

            if let Some(s2_val) = s2_readings_for_id.get(i) {
                if let Some(s2_obj) = s2_val.as_object() {
                    if let Some(temp) = s2_obj.get("temperature") { combined_reading_map.insert("temperature".to_string(), temp.clone()); }
                    if let Some(hum) = s2_obj.get("humidity") { combined_reading_map.insert("humidity".to_string(), hum.clone()); }
                }
            }

            if let Some(s3_val) = s3_readings_for_id.get(i) {
                 if let Some(s3_obj) = s3_val.as_object() {
                    if let Some(ts) = s3_obj.get("timestamp") { combined_reading_map.insert("timestamp".to_string(), ts.clone()); }
                    if let Some(econ) = s3_obj.get("energy_consume") { combined_reading_map.insert("energy_consume".to_string(), econ.clone()); }
                    if let Some(ecost) = s3_obj.get("energy_cost") { combined_reading_map.insert("energy_cost".to_string(), ecost.clone()); }
                }
            }

            if !combined_reading_map.is_empty() {
                merged_sensor_data_list.push(Value::Object(combined_reading_map));
            }
        }
        
        let valid_readings: Vec<Value> = merged_sensor_data_list.into_iter()
            .filter(|reading| !reading.is_null() && reading.is_object() && !reading.as_object().unwrap().is_empty())
            .collect();

        final_results.push(json!({
            "id": id_of_event,
            "uuid": uuid_val,
            "color": color_val,
            "sensor_data": valid_readings
        }));
    }
    
    info!("Successfully retrieved and combined data for {} newest entries based on Shard 3 timestamps.", final_results.len());
    Ok(json!(final_results))
}

// Retrieves the newest sensor data from the database.
// Input: &Graph - a reference to the Neo4j graph instance.
// Returns: Result<Value, String> - newest sensor data as JSON or an error message.
pub async fn get_newest_sensordata(graph: &Graph) -> Result<Value, String> {
    let newest_sensordata_cypher = GET_NEWEST_SENSORDATA;
    let newest_sensordata_query = query(newest_sensordata_cypher);
    
    let mut results = Vec::new();

    match graph.execute(newest_sensordata_query).await {
        Ok(mut result) => {
            while let Ok(Some(row)) = result.next().await {
                
                let id: Option<i64> = row.get("id").ok();
                
                let sensor_reading: Value = match row.get("sensor_reading") {
                    Ok(reading) => reading,
                    Err(e) => {
                        error!("Failed to get sensor_reading: {}", e);
                        continue;
                    }
                };
                
                results.push(json!({
                    "id": id,
                    "sensor_reading": sensor_reading
                }));
            }
            
            info!("Retrieved {} newest sensor readings from shard 2", results.len());
            Ok(json!(results))
        },
        Err(e) => {
            let error_msg = format!("Failed to execute GET_NEWEST_SENSORDATA query: {}", e);
            error!("{}", error_msg);
            Err(error_msg)
        }
    }
}

// Retrieves the newest energy data from the database.
// Input: &Graph - a reference to the Neo4j graph instance.
// Returns: Result<Value, String> - newest energy data as JSON or an error message.
pub async fn get_newest_energydata(graph: &Graph) -> Result<Value, String> {
    let newest_energydata_cypher = GET_NEWEST_ENERGYDATA;
    let newest_energydata_query = query(newest_energydata_cypher);
    
    let mut results = Vec::new();

    match graph.execute(newest_energydata_query).await {
        Ok(mut result) => {
            while let Ok(Some(row)) = result.next().await {
                
                let id: Option<i64> = row.get("id").ok();
                
                let energy_reading: Value = match row.get("energy_reading") {
                    Ok(reading) => reading,
                    Err(e) => {
                        error!("Failed to get energy_reading: {}", e);
                        continue;
                    }
                };
                
                results.push(json!({
                    "id": id,
                    "energy_reading": energy_reading
                }));
            }
            
            info!("Retrieved {} newest energy readings from shard 3", results.len());
            Ok(json!(results))
        },
        Err(e) => {
            let error_msg = format!("Failed to execute GET_NEWEST_ENERGYDATA query: {}", e);
            error!("{}", error_msg);
            Err(error_msg)
        }
    }
}

// Retrieves paginated IDs and their associated data from the database.
// Input: page - the page number, &Graph - a reference to the Neo4j graph instance.
// Returns: Result<Value, String> - paginated data as JSON or an error message.
pub async fn get_paginated_ids(page: usize, graph: &Graph) -> Result<Value, String> {
    
    const PAGE_SIZE: usize = 25;
    
    let count_cypher = "USE fabric.dbshard1 MATCH (id:Id) RETURN count(id) as total";
    let count_query = query(count_cypher);
    
    let total_ids = match graph.execute(count_query).await {
        Ok(mut result) => {
            match result.next().await {
                Ok(Some(row)) => {
                    match row.get::<i64>("total") {
                        Ok(count) => count,
                        Err(e) => return Err(format!("Failed to extract total count: {}", e))
                    }
                }
                Ok(None) => return Err("Count query returned no rows.".to_string()),
                Err(e) => return Err(format!("Failed to get result from count query: {}", e)),
            }
        }
        Err(e) => return Err(format!("Failed to execute count query: {}", e)),
    };
    
    let total_pages = ((total_ids as usize) + PAGE_SIZE - 1) / PAGE_SIZE; 
    
    let current_page = if page < 1 {
        1
    } else if page > total_pages && total_pages > 0 {
        total_pages
    } else {
        page
    };
    
    let skip = (current_page - 1) * PAGE_SIZE;
    
    let mut combined_results: HashMap<i64, Value> = HashMap::new();
    let mut shard2_data_map: HashMap<i64, Vec<Value>> = HashMap::new();
    let mut shard3_data_map: HashMap<i64, Vec<Value>> = HashMap::new();

    let shard1_cypher = format!(
        "USE fabric.dbshard1 
         MATCH (id_node:Id) 
         OPTIONAL MATCH (id_node)-[:HAS_UUID]->(uuid_node:Uuid)
         OPTIONAL MATCH (id_node)-[:HAS_COLOR]->(color_node:Color)
         RETURN id_node.value AS id, uuid_node.value AS uuid, color_node.value AS color
         ORDER BY id_node.value
         SKIP {} LIMIT {}", skip, PAGE_SIZE
    );
    
    match graph.execute(query(&shard1_cypher)).await {
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
            error!("Failed to execute Shard 1 query in get_paginated_ids: {}", e);
        }
    }
    
    let page_ids: Vec<i64> = combined_results.keys().cloned().collect();
    
    if page_ids.is_empty() {
        return Ok(json!({
            "total_pages": total_pages,
            "current_page": current_page,
            "page_content": []
        }));
    }
    
    let id_list = page_ids.iter()
                         .map(|id| id.to_string())
                         .collect::<Vec<String>>()
                         .join(", ");
    
    let shard2_cypher = format!(
        "USE fabric.dbshard2 
         MATCH (id_node:Id) WHERE id_node.value IN [{}]
         MATCH (id_node)-[:HAS_SENSOR_DATA]->(sensor_data_node:SensorData)
         OPTIONAL MATCH (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node:Temperature)
         OPTIONAL MATCH (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node:Humidity)
         RETURN id_node.value AS id, {{
             temperature: temp_node.value,
             humidity: hum_node.value
         }} AS sensor_reading", id_list
    );
    
    match graph.execute(query(&shard2_cypher)).await {
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
            error!("Failed to execute Shard 2 query in get_paginated_ids: {}", e);
        }
    }
    
    let shard3_cypher = format!(
        "USE fabric.dbshard3 
         MATCH (id_node:Id) WHERE id_node.value IN [{}]
         OPTIONAL MATCH (id_node)-[:HAS_TIMESTAMP]->(time_node:Timestamp)
         OPTIONAL MATCH (id_node)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node:EnergyConsumption)
         OPTIONAL MATCH (econsume_node)-[:HAS_ENERGY_COST]->(ecost_node:EnergyCost)
         RETURN id_node.value AS id, {{
             timestamp: time_node.value,
             energy_consume: econsume_node.value,
             energy_cost: ecost_node.value
         }} AS energy_reading
         ORDER BY id_node.value, time_node.value", id_list
    );
    
    match graph.execute(query(&shard3_cypher)).await {
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
            error!("Failed to execute Shard 3 query in get_paginated_ids: {}", e);
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

    let mut final_data: Vec<Value> = combined_results.into_values().collect();
    final_data.sort_by(|a, b| {
        let a_id = a.get("id").and_then(|id| id.as_i64()).unwrap_or(0);
        let b_id = b.get("id").and_then(|id| id.as_i64()).unwrap_or(0);
        a_id.cmp(&b_id)
    });
    
    info!("Retrieved and combined paginated data, page {} of {} with {} entries.", 
           current_page, total_pages, final_data.len());
    
    Ok(json!({
        "total_pages": total_pages,
        "current_page": current_page,
        "page_content": final_data
    }))
}