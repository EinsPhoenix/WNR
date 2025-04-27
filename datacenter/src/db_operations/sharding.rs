use neo4rs::{Graph, query};
use log::{error, info, warn};
use serde_json::Value; // This is serde_json::Value
use std::collections::HashMap;

use neo4rs::{Row, Result as NeoResult}; 
use serde_json::json;


async fn prepare_id_params(id: i64) -> HashMap<String, String> {
    let mut params = HashMap::new();
    params.insert("id".to_string(), id.to_string());
    params
}


async fn prepare_timestamp_params(timestamp: &str) -> HashMap<String, String> {
    let mut params = HashMap::new();
    params.insert("timestamp".to_string(), timestamp.to_string());
    params
}

async fn prepare_timestamp_range_params(start: &str, end: &str) -> HashMap<String, String> {
    let mut params = HashMap::new();
    params.insert("start_timestamp".to_string(), start.to_string());
    params.insert("end_timestamp".to_string(), end.to_string());
    params
}

async fn validate_new_item(item: &Value) -> bool {
    item.get("id").and_then(|v| v.as_f64().or_else(|| v.as_i64().map(|i| i as f64)).or_else(|| v.as_u64().map(|u| u as f64))).is_some() // Allow numeric ID types
        && item.get("uuid").and_then(|v| v.as_str()).is_some()
        && item.get("color").and_then(|v| v.as_str()).is_some()
        && item.get("sensor_data").map(|v| v.is_object()).unwrap_or(false)
        && item.get("sensor_data").and_then(|sd| sd.get("temperature")).and_then(|t| t.as_f64()).is_some()
        && item.get("sensor_data").and_then(|sd| sd.get("humidity")).and_then(|h| h.as_f64()).is_some()
        && item.get("timestamp").and_then(|v| v.as_str()).is_some()
        && item.get("energy_consume").and_then(|v| v.as_f64()).is_some()
        && item.get("energy_cost").and_then(|v| v.as_f64()).is_some()
}

async fn prepare_item_params(item: &Value) -> Option<HashMap<String, String>> {
    let mut params = HashMap::new();


    if let Some(uuid) = item.get("uuid").and_then(|v| v.as_str()) {
        params.insert("uuid".to_string(), uuid.to_string());
    } else {
        return None;
    }

    if let Some(color) = item.get("color").and_then(|v| v.as_str()) {
        params.insert("color".to_string(), color.to_string());
    } else {
        return None;
    }

    if let Some(temp) = item.get("sensor_data").and_then(|v| v.get("temperature")).and_then(|v| v.as_f64()) {
        params.insert("temperature".to_string(), temp.to_string());
    } else {
        return None;
    }

    if let Some(humidity) = item.get("sensor_data").and_then(|v| v.get("humidity")).and_then(|v| v.as_f64()) {
        params.insert("humidity".to_string(), humidity.to_string());
    } else {
        return None;
    }

    if let Some(timestamp) = item.get("timestamp").and_then(|v| v.as_str()) {
        params.insert("timestamp".to_string(), timestamp.to_string());
    } else {
        return None;
    }

    if let Some(energy_consume) = item.get("energy_consume").and_then(|v| v.as_f64()) {
        params.insert("energy_consume".to_string(), energy_consume.to_string());
    } else {
        return None;
    }

    if let Some(energy_cost) = item.get("energy_cost").and_then(|v| v.as_f64()) {
        params.insert("energy_cost".to_string(), energy_cost.to_string());
    } else {
        return None;
    }

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
       
        let shard_id = (index % 3) + 1; 
        let shard_db = format!("fabric.dbshard{}", shard_id);

        let mut params = match prepare_item_params(item).await {
            Some(p) => p,
            None => {
                
                let error_msg =
                    format!("Failed to extract parameters for item at index {}: {:?}", index, item);
                error!("{}", error_msg);
                errors.push(error_msg);
                continue; 
            }
        };

        let new_id = match acquire_global_id(graph).await {
             Ok(id) => id,
             Err(e) => {
                 let error_msg = format!("Failed to acquire global ID for item at index {}: {}", index, e);
                 error!("{}", error_msg);
                 errors.push(error_msg);
                 continue;
             }
         };

        params.insert("new_id".to_string(), new_id.to_string());

        let cypher = format!(
            r#"
           
                USE {shard_db} 

                // Use the globally unique ID passed as a parameter
                CREATE (id_node:Id {{value: toInteger($new_id)}}) 
                CREATE (uuid_node:Uuid {{value: $uuid}}) // Assuming UUID is unique per item, create new
                MERGE (color_node:Color {{value: $color}})
                MERGE (temp_node:Temperature {{value: toFloat($temperature)}})
                MERGE (hum_node:Humidity {{value: toFloat($humidity)}})
                MERGE (time_node:Timestamp {{value: $timestamp}}) // Assuming timestamp is stored as string
                MERGE (econsume_node:EnergyConsume {{value: toFloat($energy_consume)}})
                MERGE (ecost_node:EnergyCost {{value: toFloat($energy_cost)}})
                CREATE (sensor_data_node:SensorData) // Create a new SensorData node for each item

                // Create relationships
                MERGE (id_node)-[:HAS_UUID]->(uuid_node)
                MERGE (id_node)-[:HAS_COLOR]->(color_node)
                MERGE (id_node)-[:PRODUCES_SENSOR_DATA]->(sensor_data_node)
                MERGE (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node)
                MERGE (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node)
                MERGE (sensor_data_node)-[:RECORDED_AT]->(time_node)
                MERGE (sensor_data_node)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node)
                MERGE (econsume_node)-[:HAS_ENERGY_COST]->(ecost_node)

                RETURN id_node.value AS processed_id 
            
            "#,
            shard_db = shard_db 
        );

        info!("Executing query for item {} in shard {}: {}", index, shard_id, shard_db);
        
        let create_query = query(&cypher).params(params);

        match graph.execute(create_query).await {
            Ok(mut result) => {
                
                match result.next().await {
                    Ok(Some(_row)) => {
                         processed_count += 1;
                         info!("Successfully processed item {} with ID {} in shard {}", index, new_id, shard_id);
                    }
                    Ok(None) => {
                         warn!("Query for item at index {} in shard {} executed but returned no confirmation row.", index, shard_id);
                         errors.push(format!("No confirmation row for item {} in shard {}", index, shard_id));
                    }
                    Err(e) => {
                         let error_msg = format!("Failed to process result row for item at index {} in shard {}: {}", index, shard_id, e);
                         error!("{}", error_msg);
                         errors.push(error_msg);
                    }
                }
            }
            Err(e) => {
                let error_msg = format!(
                    "Failed to execute query for item at index {} in shard {}: {}",
                    index, shard_id, e
                );
                error!("{}", error_msg);
                errors.push(error_msg);
            }
        }
       
    } 

    if errors.is_empty() {
        info!(
            "Successfully processed {} out of {} items across shards.",
            processed_count,
            data_array.len()
        );
        Ok(processed_count)
    } else {
        let combined_error = format!(
            "Processed {} items with {} errors: {}",
            processed_count,
            errors.len(),
            errors.join("; ")
        );
        error!("{}", combined_error);
        
        Ok(processed_count)
        
    }
}

async fn reconstruct_item_from_row(row: &Row) -> NeoResult<Value> {
   
    let id: i64 = row.get("id").map_err(neo4rs::Error::DeserializationError)?;
    let uuid: String = row.get("uuid").map_err(neo4rs::Error::DeserializationError)?;
    let color: String = row.get("color").map_err(neo4rs::Error::DeserializationError)?;
    let temperature: f64 = row.get("temperature").map_err(neo4rs::Error::DeserializationError)?;
    let humidity: f64 = row.get("humidity").map_err(neo4rs::Error::DeserializationError)?;
    let timestamp: String = row.get("timestamp").map_err(neo4rs::Error::DeserializationError)?;
    let energy_consume: f64 = row.get("energy_consume").map_err(neo4rs::Error::DeserializationError)?;
    let energy_cost: f64 = row.get("energy_cost").map_err(neo4rs::Error::DeserializationError)?;

 
    Ok(json!({
        "id": id,
        "uuid": uuid,
        "color": color,
        "sensor_data": {
            "temperature": temperature,
            "humidity": humidity
        },
        "timestamp": timestamp,
        "energy_consume": energy_consume,
        "energy_cost": energy_cost
    }))
}

pub async fn get_item_by_id(graph: &Graph, item_id: i64) -> Result<Option<Value>, String> {
  
    let base_query = r#"
        MATCH (id_node:Id {value: toInteger($id)})
        MATCH (id_node)-[:HAS_UUID]->(uuid_node:Uuid)
        MATCH (id_node)-[:HAS_COLOR]->(color_node:Color)
        MATCH (id_node)-[:PRODUCES_SENSOR_DATA]->(sensor_data_node:SensorData)
        MATCH (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node:Temperature)
        MATCH (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node:Humidity)
        MATCH (sensor_data_node)-[:RECORDED_AT]->(time_node:Timestamp)
        MATCH (sensor_data_node)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node:EnergyConsume)
        MATCH (econsume_node)-[:HAS_ENERGY_COST]->(ecost_node:EnergyCost)
        RETURN
            id_node.value AS id,
            uuid_node.value AS uuid,
            color_node.value AS color,
            temp_node.value AS temperature,
            hum_node.value AS humidity,
            time_node.value AS timestamp,
            econsume_node.value AS energy_consume,
            ecost_node.value AS energy_cost
    "#;

  
    let full_query = format!(
        "
        CALL {{
            USE fabric.dbshard1
            {}
        }}
        RETURN id, uuid, color, temperature, humidity, timestamp, energy_consume, energy_cost
        UNION ALL
        CALL {{
            USE fabric.dbshard2
            {}
        }}
        RETURN id, uuid, color, temperature, humidity, timestamp, energy_consume, energy_cost
        UNION ALL
        CALL {{
            USE fabric.dbshard3
            {}
        }}
        RETURN id, uuid, color, temperature, humidity, timestamp, energy_consume, energy_cost
        ",
        base_query, base_query, base_query
    );

    let params = prepare_id_params(item_id).await;

    info!("Executing query to find item by ID: {}", item_id);
    match graph.execute(query(&full_query).params(params)).await {
        Ok(mut result) => {
            match result.next().await {
                Ok(Some(row)) => {
                    match reconstruct_item_from_row(&row).await { 
                        Ok(item_json) => Ok(Some(item_json)),
                        Err(e) => {
                            error!("Failed to reconstruct item from row: {}", e);
                            Err(format!("Failed to reconstruct item from row: {}", e))
                        }
                    }
                },
                Ok(None) => Ok(None), 
                Err(e) => {
                    error!("Failed to fetch result row for ID {}: {}", item_id, e);
                    Err(format!("Failed to fetch result row: {}", e))
                }
            }
        }
        Err(e) => {
            error!("Failed to execute query for ID {}: {}", item_id, e);
            Err(format!("Database query failed: {}", e))
        }
    }
}


pub async fn get_temp_humidity_by_timestamp(graph: &Graph, timestamp: &str) -> Result<Value, String> {
  
    let base_query = r#"
        MATCH (time_node:Timestamp {value: $timestamp})<-[:RECORDED_AT]-(sensor_data_node:SensorData)
        MATCH (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node:Temperature)
        MATCH (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node:Humidity)
        RETURN
            time_node.value AS timestamp,
            temp_node.value AS temperature,
            hum_node.value AS humidity
    "#;

  
    let full_query = format!(
        "
        CALL {{
            USE fabric.dbshard1
            {}
        }}
        RETURN timestamp, temperature, humidity
        UNION ALL
        CALL {{
            USE fabric.dbshard2
            {}
        }}
        RETURN timestamp, temperature, humidity
        UNION ALL
        CALL {{
            USE fabric.dbshard3
            {}
        }}
        RETURN timestamp, temperature, humidity
        ",
        base_query, base_query, base_query
    );

    let params = prepare_timestamp_params(timestamp).await;

    info!("Executing query for timestamp: {}", timestamp);
    let mut results_vec: Vec<Value> = Vec::new();
    match graph.execute(query(&full_query).params(params)).await {
        Ok(mut result) => {
            while let Ok(Some(row)) = result.next().await {
                 match (row.get::<f64>("temperature"), row.get::<f64>("humidity")) {
                    (Ok(temp), Ok(hum)) => {
                        results_vec.push(json!({
                            "temperature": temp,
                            "humidity": hum
                        }));
                    }
                    _ => {
                         let err_msg = "Failed to extract temperature/humidity from row".to_string();
                         error!("{}", err_msg);
                    }
                 }
            }
            Ok(json!(results_vec))
        }
        Err(e) => {
            error!("Failed to execute query for timestamp {}: {}", timestamp, e);
            Err(format!("Database query failed: {}", e))
        }
    }
}


pub async fn get_items_by_timestamp_range(graph: &Graph, start_timestamp: &str, end_timestamp: &str) -> Result<Value, String> {
  
    let base_query = r#"
        MATCH (time_node:Timestamp)
        WHERE time_node.value >= $start_timestamp AND time_node.value <= $end_timestamp
        MATCH (time_node)<-[:RECORDED_AT]-(sensor_data_node:SensorData)
        MATCH (sensor_data_node)<-[:PRODUCES_SENSOR_DATA]-(id_node:Id)
        MATCH (id_node)-[:HAS_UUID]->(uuid_node:Uuid)
        MATCH (id_node)-[:HAS_COLOR]->(color_node:Color)
        MATCH (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node:Temperature)
        MATCH (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node:Humidity)
        MATCH (sensor_data_node)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node:EnergyConsume)
        MATCH (econsume_node)-[:HAS_ENERGY_COST]->(ecost_node:EnergyCost)
        RETURN
            id_node.value AS id,
            uuid_node.value AS uuid,
            color_node.value AS color,
            temp_node.value AS temperature,
            hum_node.value AS humidity,
            time_node.value AS timestamp,
            econsume_node.value AS energy_consume,
            ecost_node.value AS energy_cost
    "#;


    let full_query = format!(
        "
        CALL {{
            USE fabric.dbshard1
            {}
        }}
        RETURN id, uuid, color, temperature, humidity, timestamp, energy_consume, energy_cost
        UNION ALL
        CALL {{
            USE fabric.dbshard2
            {}
        }}
        RETURN id, uuid, color, temperature, humidity, timestamp, energy_consume, energy_cost
        UNION ALL
        CALL {{
            USE fabric.dbshard3
            {}
        }}
        RETURN id, uuid, color, temperature, humidity, timestamp, energy_consume, energy_cost
        ",
        base_query, base_query, base_query
    );

    let params = prepare_timestamp_range_params(start_timestamp, end_timestamp).await;

    info!("Executing query for timestamp range: {} - {}", start_timestamp, end_timestamp);
    let mut results_vec: Vec<Value> = Vec::new();
    match graph.execute(query(&full_query).params(params)).await {
        Ok(mut result) => {
            while let Ok(Some(row)) = result.next().await {
                match reconstruct_item_from_row(&row).await {
                    Ok(item_json) => results_vec.push(item_json),
                    Err(e) => {
                        error!("Failed to reconstruct item from row in range query: {}", e);
                    }
                }
            }
            Ok(json!(results_vec))
        }
        Err(e) => {
            error!("Failed to execute query for timestamp range: {}", e);
            Err(format!("Database query failed: {}", e))
        }
    }
}

pub async fn get_all_items_sorted_by_timestamp(graph: &Graph) -> Result<Value, String> {
  
    let base_query = r#"
        MATCH (id_node:Id) // Starte von ID-Knoten
        MATCH (id_node)-[:HAS_UUID]->(uuid_node:Uuid)
        MATCH (id_node)-[:HAS_COLOR]->(color_node:Color)
        MATCH (id_node)-[:PRODUCES_SENSOR_DATA]->(sensor_data_node:SensorData)
        MATCH (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node:Temperature)
        MATCH (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node:Humidity)
        MATCH (sensor_data_node)-[:RECORDED_AT]->(time_node:Timestamp)
        MATCH (sensor_data_node)-[:HAS_ENERGY_CONSUMPTION]->(econsume_node:EnergyConsume)
        MATCH (econsume_node)-[:HAS_ENERGY_COST]->(ecost_node:EnergyCost)
        RETURN
            id_node.value AS id,
            uuid_node.value AS uuid,
            color_node.value AS color,
            temp_node.value AS temperature,
            hum_node.value AS humidity,
            time_node.value AS timestamp,
            econsume_node.value AS energy_consume,
            ecost_node.value AS energy_cost
    "#;

    let full_query = format!(
        "
        CALL {{
            USE fabric.dbshard1
            {}
        }}
        RETURN id, uuid, color, temperature, humidity, timestamp, energy_consume, energy_cost
        UNION ALL
        CALL {{
            USE fabric.dbshard2
            {}
        }}
        RETURN id, uuid, color, temperature, humidity, timestamp, energy_consume, energy_cost
        UNION ALL
        CALL {{
            USE fabric.dbshard3
            {}
        }}
        RETURN id, uuid, color, temperature, humidity, timestamp, energy_consume, energy_cost
        ORDER BY timestamp ASC // Sortiere das gesamte Ergebnis
        ",
        base_query, base_query, base_query
    );

    info!("Executing query to get all items sorted by timestamp");
    let mut results_vec: Vec<Value> = Vec::new();
    match graph.execute(query(&full_query)).await { 
        Ok(mut result) => {
            while let Ok(Some(row)) = result.next().await {
                 match reconstruct_item_from_row(&row).await {
                    Ok(item_json) => results_vec.push(item_json),
                    Err(e) => {
                        error!("Failed to reconstruct item from row in get_all query: {}", e);
                        
                    }
                }
            }
             Ok(json!(results_vec)) 
        }
        Err(e) => {
            error!("Failed to execute query for all items: {}", e);
            Err(format!("Database query failed: {}", e))
        }
    }
}