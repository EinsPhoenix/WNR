use rumqttc::AsyncClient;
use serde_json::{Value, json};
use log::{info, error, warn};
use std::error::Error;
use std::sync::Arc;

use crate::db;
use crate::db_operations::crud::{get_specific_uuid_node, get_all_uuid_nodes, get_newest_uuid, create_new_relation,get_paginated_uuids};
use crate::db_operations::specificoperations::{get_temperature_humidity_at_time, get_nodes_with_temperature_or_humidity, get_nodes_in_time_range, get_nodes_with_color, get_nodes_with_energy_cost, get_nodes_with_energy_consume};
use crate::db_operations::relationshipexport::export_all_with_relationships;

use super::publisher::{publish_result, publish_error_response}; 

pub async fn process_request(client: &AsyncClient, payload: &[u8], db_handler: &Arc<db::DatabaseCluster>) -> Result<(), Box<dyn Error>> {
    let payload_str = String::from_utf8_lossy(payload);
    info!("Received request: {}", payload_str);

    let json_value: Value = match serde_json::from_str(&payload_str) {
        Ok(value) => value,
        Err(e) => {
            error!("Failed to parse JSON: {}", e);
        
            return Err(Box::new(e));
        }
    };

    // Extract client ID 
    let requesting_client_id = match json_value.get("client_id").and_then(Value::as_str) {
        Some(id) => id.to_string(), 
        None => {
            error!("Missing client_id in request payload: {}", payload_str);
          
            
            return Err("Missing client_id".into());
        }
    };

    // Get database connections
    let read_conn_1 = db_handler.get_read_db(0).await;
    let read_conn_2 = db_handler.get_read_db(1).await;
    let write_conn = db_handler.get_primary_db().await;

    // Process based on the "request" field
    match json_value.get("request").and_then(Value::as_str) {
        Some("uuid") => {
            info!("Processing UUID request for client: {}", requesting_client_id);

            if let Some(payload_data) = json_value.get("payload") {
                if let Some(uuid_array) = payload_data.as_array() {
                    for uuid_obj in uuid_array {
                        if let Some(uuid) = uuid_obj.get("uuid").and_then(Value::as_str) {
                            info!("Processing UUID: {} for Client-ID: {}", uuid, requesting_client_id);
                            let response_topic = format!("rust/uuid/{}", requesting_client_id); 

                            match get_specific_uuid_node(uuid, &read_conn_1).await {
                                Some(node) => {
                                    info!("Found node for UUID {}", uuid);
                                    publish_result(client, &response_topic, &node).await?;
                                },
                                None => {
                                    warn!("No node found for UUID: {}", uuid); 
                                    let empty_response = json!({
                                        "uuid": uuid,
                                        "found": false,
                                        "message": "No data found for this UUID"
                                    });
                                    publish_result(client, &response_topic, &empty_response).await?;
                                }
                            }
                        } else {
                             warn!("Invalid item in UUID payload array (missing 'uuid' string): {:?}", uuid_obj);
                           
                        }
                    }
                } else {
                    error!("Invalid payload format for 'uuid' request, expected array. Client: {}", requesting_client_id);
                    return publish_error_response(client, &requesting_client_id, "uuid", "Invalid payload format, expected array").await;
                }
            } else {
                warn!("No payload provided for UUID request. Client: {}", requesting_client_id);
                return publish_error_response(client, &requesting_client_id, "uuid", "No payload provided").await;
            }
        },

        Some("all") => {
            info!("Processing 'all' request for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/all", requesting_client_id);
            match get_all_uuid_nodes(&read_conn_2).await {
                Some(all_nodes) => {
                    publish_result(client, &response_topic, &all_nodes).await?;
                },
                None => { 
                    error!("Failed to retrieve all UUID nodes for Client-ID: {}", requesting_client_id);
                    return publish_error_response(client, &requesting_client_id, "all", "Failed to get all UUID nodes").await;
                }
            }
        },

        Some("color") => {
            info!("Processing 'color' data for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/color", requesting_client_id);
            if let Some(color_data) = json_value.get("data").and_then(Value::as_str) {
                match get_nodes_with_color(color_data, &read_conn_2).await {
                    Some(processed) => { 
                        publish_result(client, &response_topic, &processed).await?;
                    },
                    None => { 
                        error!("Failed to get nodes with color '{}' for Client-ID: {}", color_data, requesting_client_id);
                        return publish_error_response(client, &requesting_client_id, "color", "Failed to get nodes with color").await;
                    }
                }
            } else {
                warn!("Missing or invalid 'data' field for 'color' request. Client: {}", requesting_client_id);
                return publish_error_response(client, &requesting_client_id, "color", "Missing or invalid 'data' field (must be a string)").await;
            }
        },

        Some("time_range") => {
            info!("Processing 'time_range' data for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/time_range", requesting_client_id);
            let start = json_value.get("start").and_then(Value::as_str);
            let end = json_value.get("end").and_then(Value::as_str);

            if let (Some(start_time), Some(end_time)) = (start, end) {
                match get_nodes_in_time_range(start_time, end_time, &read_conn_1).await {
                    Some(nodes) => {
                        publish_result(client, &response_topic, &nodes).await?;
                    },
                    None => {
                         error!("Failed to get nodes in time range ('{}' - '{}') for Client-ID: {}", start_time, end_time, requesting_client_id);
                        return publish_error_response(client, &requesting_client_id, "time_range", "Failed to get nodes in time range").await;
                    }
                }
            } else {
                 warn!("Missing or invalid 'start' or 'end' fields for 'time_range' request. Client: {}", requesting_client_id);
                return publish_error_response(client, &requesting_client_id, "time_range", "Missing or invalid 'start' or 'end' fields (must be strings)").await;
            }
        },

        Some("temperature_humidity") => {
             info!("Processing 'temperature_humidity' data for Client-ID: {}", requesting_client_id);
             let response_topic = format!("rust/response/{}/temperature_humidity", requesting_client_id);
             let temp = json_value.get("temperature").and_then(Value::as_f64);
             let humidity = json_value.get("humidity").and_then(Value::as_f64);

             if let (Some(temp_val), Some(humidity_val)) = (temp, humidity) {
                 match get_nodes_with_temperature_or_humidity(temp_val, humidity_val, &read_conn_1).await {
                     Some(nodes) => {
                         publish_result(client, &response_topic, &nodes).await?;
                     },
                     None => {
                         error!("Failed to get nodes with temp {} / humidity {} for Client-ID: {}", temp_val, humidity_val, requesting_client_id);
                         return publish_error_response(client, &requesting_client_id, "temperature_humidity", "Failed to get nodes with temperature and humidity").await;
                     }
                 }
             } else {
                 warn!("Missing or invalid 'temperature' or 'humidity' fields for 'temperature_humidity' request. Client: {}", requesting_client_id);
                 return publish_error_response(client, &requesting_client_id, "temperature_humidity", "Missing or invalid 'temperature' or 'humidity' fields (must be numbers)").await;
             }
        },

        Some("timestamp") => {
            info!("Processing 'timestamp' data for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/timestamp", requesting_client_id);
            if let Some(timestamp) = json_value.get("data").and_then(Value::as_str) {
                match get_temperature_humidity_at_time(&read_conn_1, timestamp).await {
                    Some((temp, humidity)) => {
                        let response = json!({
                            "timestamp": timestamp,
                            "temperature": temp, 
                            "humidity": humidity
                        });
                        publish_result(client, &response_topic, &response).await?;
                    },
                    None => { 
                        warn!("No temperature/humidity data found for timestamp '{}'. Client: {}", timestamp, requesting_client_id);
                        
                         let not_found_response = json!({
                             "timestamp": timestamp,
                             "found": false,
                             "message": "No temperature/humidity data found for this timestamp"
                         });
                         publish_result(client, &response_topic, &not_found_response).await?;
                       
                    }
                }
            } else {
                warn!("Missing or invalid 'data' field for 'timestamp' request. Client: {}", requesting_client_id);
                return publish_error_response(client, &requesting_client_id, "timestamp", "Missing or invalid 'data' field (must be a string)").await;
            }
        },

        Some("energy_cost") => {
            info!("Processing 'energy_cost' data for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/energy_cost", requesting_client_id);
            if let Some(cost) = json_value.get("data").and_then(Value::as_f64) {
                match get_nodes_with_energy_cost(cost, &read_conn_2).await {
                    Some(nodes) => {
                        publish_result(client, &response_topic, &nodes).await?;
                    },
                    None => {
                        error!("Failed to get nodes with energy cost >= {} for Client-ID: {}", cost, requesting_client_id);
                        return publish_error_response(client, &requesting_client_id, "energy_cost", "Failed to get nodes with energy cost").await;
                    }
                }
            } else {
                warn!("Missing or invalid 'data' field for 'energy_cost' request. Client: {}", requesting_client_id);
                return publish_error_response(client, &requesting_client_id, "energy_cost", "Missing or invalid 'data' field (must be a number)").await;
            }
        },

        Some("energy_consume") => {
            info!("Processing 'energy_consume' data for Client-ID: {}", requesting_client_id);
             let response_topic = format!("rust/response/{}/energy_consume", requesting_client_id);
            if let Some(consume) = json_value.get("data").and_then(Value::as_f64) {
                match get_nodes_with_energy_consume(consume, &read_conn_2).await {
                    Some(nodes) => {
                        publish_result(client, &response_topic, &nodes).await?;
                    },
                    None => {
                         error!("Failed to get nodes with energy consumption >= {} for Client-ID: {}", consume, requesting_client_id);
                        return publish_error_response(client, &requesting_client_id, "energy_consume", "Failed to get nodes with energy consumption").await;
                    }
                }
            } else {
                 warn!("Missing or invalid 'data' field for 'energy_consume' request. Client: {}", requesting_client_id);
                return publish_error_response(client, &requesting_client_id, "energy_consume", "Missing or invalid 'data' field (must be a number)").await;
            }
        },

        Some("newest") => {
            info!("Processing 'newest' request for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/newest", requesting_client_id);
            match get_newest_uuid(&read_conn_1).await {
                Some(nodes) => { 
                    publish_result(client, &response_topic, &nodes).await?;
                },
                None => { 
                    error!("Failed to get newest nodes for Client-ID: {}", requesting_client_id);
                    return publish_error_response(client, &requesting_client_id, "newest", "Failed to get newest nodes").await;
                }
            }
        },

        Some("add") => {
            info!("Processing 'add' data for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/add", requesting_client_id);
            if let Some(add_data) = json_value.get("data") { 
                match create_new_relation(add_data, &write_conn).await {
                    Ok(true) => {
                        let response = json!({
                            "status": "success",
                            "message": "Nodes/relations successfully added/updated"
                        });
                        publish_result(client, &response_topic, &response).await?;
                    },
                    Ok(false) => {
                       
                        info!("No new nodes created or relations added (data might already exist or update occurred). Client-ID: {}", requesting_client_id);
                        let response = json!({
                            "status": "no_change", 
                            "message": "No new nodes or relations were created (data might already exist or represent an update)"
                        });
                        publish_result(client, &response_topic, &response).await?;
                    },
                    Err(err) => {
                        error!("Failed to add/update nodes/relations for Client-ID: {}. Error: {}", requesting_client_id, err);
                        return publish_error_response(client, &requesting_client_id, "add", &format!("Failed to process add request: {}", err)).await;
                    }
                }
            } else {
                 warn!("Missing 'data' field for 'add' request. Client: {}", requesting_client_id);
                return publish_error_response(client, &requesting_client_id, "add", "Missing 'data' field").await;
            }
        },

        Some("relation") => {
            info!("Processing 'relation' data export for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/relation", requesting_client_id);
           
            match export_all_with_relationships(&read_conn_1, Some(1000)).await { 
                Some(nodes) => {
                    publish_result(client, &response_topic, &nodes).await?;
                },
                None => {
                    error!("Failed to get relationship data for Client-ID: {}", requesting_client_id);
                    return publish_error_response(client, &requesting_client_id, "relation", "Failed to get relationship data").await;
                }
            }
        },

        Some("page") => {
            info!("Processing 'page' data for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/page", requesting_client_id);
           
            if let Some(page_number) = json_value.get("data").and_then(Value::as_u64).map(|v| v as usize) {
               
                 let page_index = if page_number > 0 { page_number - 1 } else { 0 };
                match get_paginated_uuids(&read_conn_2, page_index).await { 
                    Some(nodes) => {
                        publish_result(client, &response_topic, &nodes).await?;
                    },
                    None => {
                        error!("Failed to get paginated data (page {}) for Client-ID: {}", page_number, requesting_client_id);
                        return publish_error_response(client, &requesting_client_id, "page", "Failed to get paginated data").await;
                    }
                }
            } else {
                 warn!("Missing or invalid 'data' field for 'page' request. Client: {}", requesting_client_id);
                return publish_error_response(client, &requesting_client_id, "page", "Missing or invalid 'data' field (must be a positive integer page number)").await;
            }
        },

        Some("topic") => { 
            warn!("'topic' request type received but not implemented. Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/topic", requesting_client_id); 
            let response = json!({
                "status": "not_implemented",
                "message": "Topic request handling is not implemented"
            });
            publish_result(client, &response_topic, &response).await?;
        },

        Some(other) => {
            warn!("Unknown request type: '{}' from Client-ID: {}", other, requesting_client_id);
           
            let response_topic = format!("rust/response/{}", requesting_client_id);
            let response = json!({
                "status": "error",
                "message": format!("Unknown request type: {}", other)
            });
            publish_result(client, &response_topic, &response).await?;
        },

        None => {
            error!("Missing 'request' field in payload from Client-ID: {}. Payload: {}", requesting_client_id, payload_str);
          
             let response_topic = format!("rust/response/{}", requesting_client_id);
             return publish_error_response(client, &requesting_client_id, "unknown", "Missing 'request' field in payload").await;
            
        }
    }

    Ok(())
}