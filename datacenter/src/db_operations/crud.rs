use neo4rs::{Graph, query};
use log::{error, info, warn};
use serde_json::{json, Value};
use std::collections::HashMap;

pub async fn validate_and_get_data_array<'a>(data: &'a Value) -> Result<&'a Vec<Value>, String> {
    
    let data_array = if data.is_array() {
        data.as_array()
    } else {
        data.get("data").and_then(|d| d.as_array())
    };

    match data_array {
        Some(array) => {
            
            if array.is_empty() {
                info!("Received empty data array. Proceeding.");
                return Ok(array);
            }

            for item in array {
                if !validate_item(item).await {
                    let error_msg = format!("Invalid item in data array: {:?}", item);
                    error!("{}", error_msg);
                    return Err(error_msg);
                }
            }
            Ok(array) 
        }
        None => {
            let error_msg = "Input data is not an array and does not contain a 'data' key with an array value.".to_string();
            info!("{}", error_msg); 
            Err(error_msg)
        }
    }
}

async fn validate_item(item: &Value) -> bool {
    item.get("uuid").and_then(|v| v.as_str()).is_some()
        && item.get("color").and_then(|v| v.as_str()).is_some()
        && item.get("sensor_data").map(|v| v.is_object()).unwrap_or(false)
        && item.get("sensor_data").and_then(|sd| sd.get("temperature")).and_then(|t| t.as_f64()).is_some()
        && item.get("sensor_data").and_then(|sd| sd.get("humidity")).and_then(|h| h.as_f64()).is_some()
        && item.get("timestamp").and_then(|v| v.as_str()).is_some()
        && item.get("energy_consume").and_then(|v| v.as_f64()).is_some()
        && item.get("energy_cost").and_then(|v| v.as_f64()).is_some()
        && item.get("id").and_then(|v| v.as_f64()).is_some()
}

//create function
pub async fn create_new_relation(data: &Value, graph: &Graph) -> Result<bool, String> {
    
    let data_array = validate_and_get_data_array(data).await?;

    if data_array.is_empty() {
        info!("Received empty validated data array. No nodes will be created.");
        return Ok(false);
    }
  
    let neo4j_data: Vec<HashMap<String, Value>> = data_array.iter().map(|item| {
        let mut record = HashMap::new();
        if let Some(uuid) = item.get("uuid").and_then(|v| v.as_str()) {
            record.insert("uuid".to_string(), Value::String(uuid.to_string()));
        }
        if let Some(color) = item.get("color").and_then(|v| v.as_str()) {
            record.insert("color".to_string(), Value::String(color.to_string()));
        }
        if let Some(timestamp) = item.get("timestamp").and_then(|v| v.as_str()) {
            record.insert("timestamp".to_string(), Value::String(timestamp.to_string()));
        }
        if let Some(energy_consume) = item.get("energy_consume").and_then(|v| v.as_f64()) {
            if let Some(num) = serde_json::Number::from_f64(energy_consume) {
                record.insert("energy_consume".to_string(), Value::Number(num));
            }
        }
        if let Some(energy_cost) = item.get("energy_cost").and_then(|v| v.as_f64()) {
            if let Some(num) = serde_json::Number::from_f64(energy_cost) {
                record.insert("energy_cost".to_string(), Value::Number(num));
            }
        }

        if let Some(id) = item.get("id").and_then(|v| v.as_f64()) {
            if let Some(num) = serde_json::Number::from_f64(id) {
                record.insert("id".to_string(), Value::Number(num));
            }
        }

        if let Some(sensor_data) = item.get("sensor_data").and_then(|v| v.as_object()) {
            if let Some(temp) = sensor_data.get("temperature").and_then(|v| v.as_f64()) {
                if let Some(num) = serde_json::Number::from_f64(temp) {
                    record.insert("sensor_data.temperature".to_string(), Value::Number(num));
                }
            }
            if let Some(humidity) = sensor_data.get("humidity").and_then(|v| v.as_f64()) {
                if let Some(num) = serde_json::Number::from_f64(humidity) {
                    record.insert("sensor_data.humidity".to_string(), Value::Number(num));
                }
            }
        }
        record
    }).collect();

    let json_data = match serde_json::to_string(&neo4j_data) {
        Ok(s) => s,
        Err(e) => {
            let error_msg = format!("Failed to serialize data: {}", e);
            error!("{}", error_msg);
            return Err(error_msg);
        }
    };

    let creation_query = query(r#"
        WITH apoc.convert.fromJsonList($data) AS records
        UNWIND records AS record
        OPTIONAL MATCH (existingUuid:UUID {id: record.uuid})
        WITH record, existingUuid
        WHERE existingUuid IS NULL
        MERGE (uuid:UUID {id: record.uuid})
        SET uuid.energy_consume = record.energy_consume,
            uuid.energy_cost = record.energy_cost,
            uuid.color = record.color,
            uuid.timestamp = record.timestamp,
            uuid.temperature = record.`sensor_data.temperature`,
            uuid.humidity = record.`sensor_data.humidity`
        MERGE (color:Color {value: record.color})
        MERGE (uuid)-[:HAS_COLOR]->(color)
        MERGE (temperature:Temperature {value: record.`sensor_data.temperature`})
        MERGE (uuid)-[:HAS_TEMPERATURE]->(temperature)
        MERGE (humidity:Humidity {value: record.`sensor_data.humidity`})
        MERGE (uuid)-[:HAS_HUMIDITY]->(humidity)
        MERGE (timestamp:Timestamp {value: record.timestamp})
        MERGE (uuid)-[:HAS_TIMESTAMP]->(timestamp)
        MERGE (timestamp)-[:SENSOR_DATA]->(temperature)
        MERGE (timestamp)-[:SENSOR_DATA]->(humidity)
        MERGE (energyCost:EnergyCost {value: record.energy_cost})
        MERGE (uuid)-[:HAS_ENERGYCOST]->(energyCost)
        MERGE (timestamp)-[:HAS_PRICE]->(energyCost)
        MERGE (energyConsume:EnergyConsume {value: record.energy_consume})
        MERGE (uuid)-[:HAS_ENERGYCONSUME]->(energyConsume)
        RETURN uuid.id AS processed_uuid
    "#)
    .param("data", json_data);

    match graph.execute(creation_query).await {
        Ok(mut result) => {
            let mut processed_count = 0;
            while let Ok(Some(_)) = result.next().await {
                processed_count += 1;
            }
            if processed_count > 0 {
                info!("Processed: {} Node(s)", processed_count);
                Ok(true)
            } else {
                let warning_msg = "No new Nodes were created (UUIDs might already exist or data was empty)";
                warn!("{}", warning_msg);
                Ok(false) 
            }
        }
        Err(e) => {
            let error_msg = format!("Failed to execute Neo4j query: {}", e);
            error!("{}", error_msg);
            Err(error_msg)
        }
    }
}

pub async fn get_specific_uuid_node(uuid: &str, graph: &Graph) -> Option<Value> {
   
    let query = query(r#"
        MATCH (uuidNode:UUID {id: $uuid})
        RETURN uuidNode.id AS uuid,
            uuidNode.color AS color,
            uuidNode.temperature AS temperature,
            uuidNode.humidity AS humidity,
            uuidNode.timestamp AS timestamp,
            uuidNode.energy_consume AS energy_consume,
            uuidNode.energy_cost AS energy_cost
        LIMIT 1
    "#)
    .param("uuid", uuid);

    match graph.execute(query).await {
        Ok(mut result) => {
            if let Ok(Some(row)) = result.next().await {
              
                let uuid_val: String = row.get("uuid").unwrap_or_default();
                let color_val: String = row.get("color").unwrap_or_default();
                let temperature: f64 = row.get("temperature").unwrap_or(0.0);
                let humidity: f64 = row.get("humidity").unwrap_or(0.0);
                let timestamp_val: String = row.get("timestamp").unwrap_or_default();
                let energy_consume: f64 = row.get("energy_consume").unwrap_or(0.0);
                let energy_cost: f64 = row.get("energy_cost").unwrap_or(0.0);

                Some(json!({
                    "uuid": uuid_val,
                    "color": color_val,
                    "sensor_data": {
                        "temperature": temperature,
                        "humidity": humidity
                    },
                    "timestamp": timestamp_val,
                    "energy_consume": energy_consume,
                    "energy_cost": energy_cost
                }))
            } else {
                None
            }
        },
        Err(e) => {
            error!("Failed to execute Neo4j query: {}", e);
            None
        }
    }
}

pub async fn get_all_uuid_nodes(graph: &Graph) -> Option<Value> {
    let query = query(r#"
        MATCH (uuidNode:UUID)
        RETURN uuidNode.id AS uuid,
            uuidNode.color AS color,
            { temperature: uuidNode.temperature, humidity: uuidNode.humidity } AS sensor_data,
            uuidNode.timestamp AS timestamp,
            uuidNode.energy_consume AS energy_consume,
            uuidNode.energy_cost AS energy_cost
        ORDER BY uuidNode.timestamp DESC
    "#);

    match graph.execute(query).await {
        Ok(mut result) => {
            let mut uuids = Vec::new();
            while let Ok(Some(row)) = result.next().await {
                let uuid_val: String = row.get("uuid").unwrap_or_default();
                let color_val: String = row.get("color").unwrap_or_default();
                let sensor_data: Value = row.get("sensor_data").unwrap_or(json!({}));
                let timestamp_val: String = row.get("timestamp").unwrap_or_default();
                let energy_consume: f64 = row.get("energy_consume").unwrap_or(0.0);
                let energy_cost: f64 = row.get("energy_cost").unwrap_or(0.0);

                uuids.push(json!({
                    "uuid": uuid_val,
                    "color": color_val,
                    "sensor_data": {
                        "temperature": sensor_data["temperature"].as_f64().unwrap_or(0.0),
                        "humidity": sensor_data["humidity"].as_f64().unwrap_or(0.0)
                    },
                    "timestamp": timestamp_val,
                    "energy_consume": energy_consume,
                    "energy_cost": energy_cost
                }));
            }

            info!("Returned nodes count: {}", uuids.len());

            Some(json!(uuids))
        },
        Err(e) => {
            error!("Failed to execute Neo4j query: {}", e);
            None
        }
    }
}

pub async fn get_paginated_uuids(graph: &Graph, page: usize) -> Option<Value> {
    const PAGE_SIZE: usize = 25;
    
    let count_query = query(r#"
        MATCH (uuidNode:UUID)
        RETURN count(uuidNode) AS total
    "#);
    
    let total_count = match graph.execute(count_query).await {
        Ok(mut result) => {
            if let Ok(Some(row)) = result.next().await {
                let count: i64 = row.get("total").unwrap_or(0);
                count as usize
            } else {
                0
            }
        },
        Err(e) => {
            error!("Failed to execute count query: {}", e);
            return None;
        }
    };
    
    let total_pages = if total_count == 0 {
        0
    } else {
        (total_count + PAGE_SIZE - 1) / PAGE_SIZE 
    };
    
    let skip = page * PAGE_SIZE;
    
    let data_query = query(r#"
        MATCH (uuidNode:UUID)-[:HAS_TIMESTAMP]->(timestamp:Timestamp)
        WITH uuidNode, timestamp
        ORDER BY timestamp.value DESC
        RETURN 
            uuidNode.id AS uuid,
            uuidNode.color AS color,
            uuidNode.temperature AS temperature,
            uuidNode.humidity AS humidity,
            uuidNode.timestamp AS timestamp,
            uuidNode.energy_consume AS energy_consume,
            uuidNode.energy_cost AS energy_cost
        SKIP $skip
        LIMIT $limit
    "#)
    .param("skip", skip as i64)
    .param("limit", PAGE_SIZE as i64);
    
    match graph.execute(data_query).await {
        Ok(mut result) => {
            let mut nodes = Vec::new();
            while let Ok(Some(row)) = result.next().await {
                
                let node = json!({
                    "uuid": row.get::<Value>("uuid").unwrap_or(Value::Null),
                    "color": row.get::<Value>("color").unwrap_or(Value::Null),
                    "temperature": row.get::<Value>("temperature").unwrap_or(Value::Null),
                    "humidity": row.get::<Value>("humidity").unwrap_or(Value::Null),
                    "timestamp": row.get::<Value>("timestamp").unwrap_or(Value::Null),
                    "energy_consume": row.get::<Value>("energy_consume").unwrap_or(Value::Null),
                    "energy_cost": row.get::<Value>("energy_cost").unwrap_or(Value::Null)
                });
                nodes.push(node);
            }
            
            info!("Returning page {} of {} with {} UUIDs", 
                  page, total_pages, nodes.len());
            
            Some(json!({
                "nodes": nodes,
                "pagination": {
                    "total_count": total_count,
                    "total_pages": total_pages,
                    "current_page": page,
                    "page_size": PAGE_SIZE
                }
            }))
        },
        Err(e) => {
            error!("Failed to execute Neo4j query: {}", e);
            None
        }
    }
}

pub async fn get_newest_uuid(graph: &Graph) -> Option<Value> {
    let query = query(r#"
        MATCH (uuidNode:UUID)-[:HAS_TIMESTAMP]->(timestamp:Timestamp)
        WITH uuidNode, timestamp
        ORDER BY timestamp.value DESC
        RETURN uuidNode.id AS uuid
        LIMIT 50
    "#);
    
    match graph.execute(query).await {
        Ok(mut result) => {
            let mut uuids = Vec::new();
            while let Ok(Some(row)) = result.next().await {
                let node: Value = row.get("uuid").unwrap();
                uuids.push(node);
            }
            Some(json!(uuids))
        },
        Err(e) => {
            error!("Failed to execute Neo4j query: {}", e);
            None
        }
    }
}

pub async fn delete_uuid_nodes(graph: &Graph, uuids: &[String]) -> Result<usize, String> {
    if uuids.is_empty() {
        info!("Received empty UUID list. No nodes will be deleted.");
        return Ok(0);
    }
    info!("Attempting to delete nodes with UUIDs: {:?}", uuids);

    let deletion_query = query(r#"
        UNWIND $uuids AS uuid_to_delete_id
        MATCH (uuid:UUID {id: uuid_to_delete_id})
        OPTIONAL MATCH (uuid)-[r]-(orphan)
        WHERE NOT orphan:UUID AND size((orphan)--()) = 1
        WITH uuid, collect(distinct orphan) AS orphans_to_delete
        WITH collect({uuid_node: uuid, orphans: orphans_to_delete}) AS items_to_delete
        UNWIND items_to_delete AS item
        DETACH DELETE item.uuid_node
        FOREACH (o IN item.orphans | DETACH DELETE o)
        RETURN size(items_to_delete) as deleted_count
    "#)
    .param("uuids", uuids); 

    match graph.execute(deletion_query).await {
        Ok(mut result) => {
            
            if let Ok(Some(row)) = result.next().await {
                let deleted_count: i64 = row.get("deleted_count").unwrap_or(0);
                let count = deleted_count as usize;
                if count > 0 {
                    info!("Successfully deleted {} node(s) matching the provided UUIDs.", count);
                } else {
                    warn!("No nodes found matching the provided UUIDs for deletion: {:?}", uuids);
                }
                Ok(count) 
            } else {
                warn!("Deletion query did not return the expected count. Assuming 0 nodes deleted for UUIDs: {:?}", uuids);
                Ok(0)
            }
        }
        Err(e) => {
            let error_msg = format!("Failed to execute deletion query for UUIDs {:?}: {}", uuids, e);
            error!("{}", error_msg);
            Err(error_msg)
        }
    }
}
