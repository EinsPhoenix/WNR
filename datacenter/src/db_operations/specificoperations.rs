use neo4rs::{Graph, query};
use log::{error, info};
use serde_json::{json, Value};
use crate::db_operations::cypher_queries::{
    GET_TEMPERATURE_HUMIDITY_AT_TIME, GET_NODES_IN_TIME_RANGE,
    GET_NODES_WITH_TEMPERATURE_OR_HUMIDITY, GET_NODES_WITH_ENERGY_COST,
    GET_NODES_WITH_ENERGY_CONSUME, GET_NODES_WITH_COLOR
};

// Retrieves temperature and humidity at a specific timestamp.
// Input: &Graph - a reference to the Neo4j graph instance, timestamp - the target timestamp as a string.
// Returns: Option<(f64, f64)> - a tuple containing temperature and humidity or None if not found.
pub async fn get_temperature_humidity_at_time(graph: &Graph, timestamp: &str) -> Option<(f64, f64)> {
    let cypher_query = query(GET_TEMPERATURE_HUMIDITY_AT_TIME)
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

// Retrieves nodes within a specific time range.
// Input: start - start timestamp, end - end timestamp, &Graph - a reference to the Neo4j graph instance.
// Returns: Option<Value> - a JSON array of UUIDs or None if no nodes are found.
pub async fn get_nodes_in_time_range(start: &str, end: &str, graph: &Graph) -> Option<Value> {
    let cypher_query = query(GET_NODES_IN_TIME_RANGE)
        .param("start", start)
        .param("end", end);

    match graph.execute(cypher_query).await {
        Ok(mut result) => {
            let mut uuids = Vec::new();
            while let Ok(Some(row)) = result.next().await {
                let uuid: i64 = row.get("uuid").unwrap_or_default();
                uuids.push(json!({"id": uuid}));
            }
            Some(json!(uuids))
        },
        Err(e) => {
            error!("Failed to execute Neo4j query: {}", e);
            None
        }
    }
}

// Retrieves nodes with a specific temperature or humidity value.
// Input: temp - temperature value, humidity - humidity value, &Graph - a reference to the Neo4j graph instance.
// Returns: Option<Value> - a JSON array of UUIDs or None if no nodes are found.
pub async fn get_nodes_with_temperature_or_humidity(temp: f64, humidity: f64, graph: &Graph) -> Option<Value> {
    let cypher_query = query(GET_NODES_WITH_TEMPERATURE_OR_HUMIDITY)
        .param("temp", temp)
        .param("humidity", humidity);

    match graph.execute(cypher_query).await {
        Ok(mut result) => {
            let mut uuids = Vec::new();
            while let Ok(Some(row)) = result.next().await {
                let uuid: i64 = row.get("uuid").unwrap_or_default();
                uuids.push(json!({"id": uuid}));
            }
            Some(json!(uuids))
        },
        Err(e) => {
            error!("Failed to execute Neo4j query: {}", e);
            None
        }
    }
}

// Retrieves nodes with a specific energy cost value.
// Input: energy_cost - the target energy cost, &Graph - a reference to the Neo4j graph instance.
// Returns: Option<Value> - a JSON array of UUIDs or None if no nodes are found.
pub async fn get_nodes_with_energy_cost(energy_cost: f64, graph: &Graph) -> Option<Value> {
    let cypher_query = query(GET_NODES_WITH_ENERGY_COST)
        .param("energy_cost", energy_cost);

    match graph.execute(cypher_query).await {
        Ok(mut result) => {
            let mut uuids = Vec::new();
            while let Ok(Some(row)) = result.next().await {
                let uuid: i64 = row.get("uuid").unwrap_or_default();
                uuids.push(json!({"id": uuid}));
            }
            Some(json!(uuids))
        },
        Err(e) => {
            error!("Failed to execute Neo4j query: {}", e);
            None
        }
    }
}

// Retrieves nodes with a specific energy consumption value.
// Input: energy_consume - the target energy consumption, &Graph - a reference to the Neo4j graph instance.
// Returns: Option<Value> - a JSON array of UUIDs or None if no nodes are found.
pub async fn get_nodes_with_energy_consume(energy_consume: f64, graph: &Graph) -> Option<Value> {
    let cypher_query = query(GET_NODES_WITH_ENERGY_CONSUME)
        .param("energy_consume", energy_consume);

    match graph.execute(cypher_query).await {
        Ok(mut result) => {
            let mut uuids = Vec::new();
            while let Ok(Some(row)) = result.next().await {
                let uuid: i64 = row.get("uuid").unwrap_or_default();
                uuids.push(json!({"id": uuid}));
            }
            Some(json!(uuids))
        },
        Err(e) => {
            error!("Failed to execute Neo4j query: {}", e);
            None
        }
    }
}

// Retrieves nodes with a specific color.
// Input: color - the target color as a string, &Graph - a reference to the Neo4j graph instance.
// Returns: Option<Value> - a JSON array of nodes with their ID, UUID, and color or None if no nodes are found.
pub async fn get_nodes_with_color(color: &str, graph: &Graph) -> Option<Value> {
    let cypher_query = query(GET_NODES_WITH_COLOR)
        .param("color", color);

    match graph.execute(cypher_query).await {
        Ok(mut result) => {
            let mut nodes_data = Vec::new();
            while let Ok(Some(row)) = result.next().await {
                let id_val: i64 = row.get("id").unwrap_or_default();
                let uuid_val: String = row.get("uuid").unwrap_or_default();
                let color_val: String = row.get("color").unwrap_or_default();

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