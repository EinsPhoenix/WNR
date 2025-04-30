use neo4rs::{Graph, query};
use log::{error, info};
use serde_json::{json, Value};

pub async fn get_temperature_humidity_at_time(graph: &Graph, timestamp: &str) -> Option<(f64, f64)> {
    let cypher_query = query(r#"
        MATCH (t:Timestamp {value: $timestamp})-[:SENSOR_DATA]->(temp:Temperature),
              (t)-[:SENSOR_DATA]->(hum:Humidity)
        RETURN temp.value AS temperature, hum.value AS humidity
    "#)
    .param("timestamp", timestamp);

    match graph.execute(cypher_query).await {
        Ok(mut result) => {
            if let Ok(Some(row)) = result.next().await {
                let temperature: f64 = row.get("temperature").unwrap_or_default();
                let humidity: f64 = row.get("humidity").unwrap_or_default();
                return Some((temperature, humidity));
            }
            None
        }
        Err(e) => {
            error!("Failed to execute Neo4j query: {}", e);
            None
        }
    }
}

// Funktion, um alle Nodes innerhalb eines Zeitraums zu bekommen
pub async fn get_nodes_in_time_range(start: &str, end: &str, graph: &Graph) -> Option<Value> {
    let query = query(r#"
        MATCH (uuid:UUID)-[:HAS_TIMESTAMP]->(timestamp:Timestamp)
        WHERE timestamp.value >= $start AND timestamp.value <= $end
        RETURN uuid
    "#)
    .param("start", start)
    .param("end", end);

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

// Funktion, um alle Nodes mit einer bestimmten Temperatur oder Luftfeuchtigkeit zu bekommen
pub async fn get_nodes_with_temperature_or_humidity(temp: f64, humidity: f64, graph: &Graph) -> Option<Value> {
    let query = query(r#"
        MATCH (uuid:UUID)-[:HAS_TEMPERATURE]->(temperature:Temperature {value: $temp}),
              (uuid)-[:HAS_HUMIDITY]->(humidity:Humidity {value: $humidity})
        RETURN uuid
    "#)
    .param("temp", temp)
    .param("humidity", humidity);

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

// Funktion, um alle Nodes mit einer bestimmten Energiekosten zu bekommen
pub async fn get_nodes_with_energy_cost(energy_cost: f64, graph: &Graph) -> Option<Value> {
    let query = query(r#"
        MATCH (uuid:UUID)-[:HAS_ENERGYCOST]->(energyCost:EnergyCost {value: $energy_cost})
        RETURN uuid
    "#)
    .param("energy_cost", energy_cost);

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

// Funktion, um alle Nodes mit einem bestimmten Energieverbrauch zu bekommen
pub async fn get_nodes_with_energy_consume(energy_consume: f64, graph: &Graph) -> Option<Value> {
    let query = query(r#"
        MATCH (uuid:UUID)-[:HAS_ENERGYCONSUME]->(energyConsume:EnergyConsume {value: $energy_consume})
        RETURN uuid
    "#)
    .param("energy_consume", energy_consume);

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

// Funktion, um alle Nodes mit einer bestimmten Farbe zu bekommen
pub async fn get_nodes_with_color(color: &str, graph: &Graph) -> Option<Value> {
    
    let query = query(r#"
        USE fabric.dbshard1
        MATCH (id_node)-[:HAS_COLOR]->(color_node:Color {value: $color})
        OPTIONAL MATCH (id_node)-[:HAS_UUID]->(uuid_node:Uuid)
        RETURN id_node.value AS id, uuid_node.value AS uuid, color_node.value AS color
    "#)
    .param("color", color);

    match graph.execute(query).await {
        Ok(mut result) => {
           
            let mut nodes_data = Vec::new();
            while let Ok(Some(row)) = result.next().await {
               
                let id_val: Value = row.get("id").unwrap_or(Value::Null);
                let uuid_val: Value = row.get("uuid").unwrap_or(Value::Null);
                let color_val: Value = row.get("color").unwrap_or(Value::Null);

                nodes_data.push(json!({
                    "id": id_val,
                    "uuid": uuid_val,
                    "color": color_val
                }));
            }
            info!("Found {} nodes with color {}", nodes_data.len(), color);
            Some(json!(nodes_data))
        },
        Err(e) => {
            error!("Failed to execute Neo4j query: {}", e);
            None
        }
    }
}
