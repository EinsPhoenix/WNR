use rumqttc::AsyncClient;
use serde_json::{Value, json};
use log::{info, error, warn};
use std::error::Error;
use std::sync::Arc;
use chrono::{Duration, Local};

use crate::db;
use crate::db_operations::specificoperations::*;
use crate::db_operations::relationshipexport::*;

use crate::db_operations::sharding::*;
use crate::db_operations::crud::*;

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

    
    let requesting_client_id = match json_value.get("client_id").and_then(Value::as_str) {
        Some(id) => id.to_string(), 
        None => {
            error!("Missing client_id in request payload: {}", payload_str);
          
            return Err("Missing client_id".into());
        }
    };

    
    let write_conn = db_handler.get_main_db().await;

    
    match json_value.get("request").and_then(Value::as_str) {
        Some("uuid") => {
            info!("Processing UUID request for client: {}", requesting_client_id);

            if let Some(payload_data) = json_value.get("data") {
                if let Some(uuid_array) = payload_data.as_array() {
                    for uuid_obj in uuid_array {
                        if let Some(uuid) = uuid_obj.get("uuid").and_then(Value::as_i64) {
                            info!("Processing UUID: {} for Client-ID: {}", uuid, requesting_client_id);
                            let response_topic = format!("rust/uuid/{}", requesting_client_id); 

                            match get_data_by_id(uuid, &write_conn).await {
                                Ok(node) => {
                                    info!("Found node for UUID {}", uuid);
                                    publish_result(client, &response_topic, &node).await?;
                                },
                                Err(e) => {
                                    warn!("No node found for UUID: {}: {}", uuid, e); 
                                    let empty_response = json!({
                                        "uuid": uuid,
                                        "found": false,
                                        "message": format!("No data found for this UUID: {}", e)
                                    });
                                    publish_result(client, &response_topic, &empty_response).await?;
                                },
                                
                            }
                        } else {
                             warn!("Invalid item in UUID payload array (missing 'uuid' i64): {:?}", uuid_obj);
                           
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
            match get_all_data(&write_conn).await {
                Ok(all_nodes) => {
                    publish_result(client, &response_topic, &all_nodes).await?;
                },
                Err(e) => { 
                    error!("Failed to retrieve all UUID nodes for Client-ID: {}: {}", requesting_client_id, e);
                    return publish_error_response(client, &requesting_client_id, "all", &format!("Failed to get all UUID nodes: {}", e)).await;
                }
            }
        },

        Some("color") => {
            info!("Processing 'color' data for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/color", requesting_client_id);
            if let Some(color_data) = json_value.get("data").and_then(Value::as_str) {
                match get_nodes_with_color(color_data, &write_conn).await {
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
                match get_nodes_in_time_range(start_time, end_time, &write_conn).await {
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
                 match get_nodes_with_temperature_or_humidity(temp_val, humidity_val, &write_conn).await {
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
                match get_temperature_humidity_at_time(&write_conn, timestamp).await {
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

        Some("id_energy_cost") => {
            info!("Processing 'energy_cost' data for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/energy_cost", requesting_client_id);
            if let Some(cost) = json_value.get("data").and_then(Value::as_f64) {
                match get_nodes_with_energy_cost(cost, &write_conn).await {
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

        Some("id_energy_consume") => {
            info!("Processing 'energy_consume' data for Client-ID: {}", requesting_client_id);
             let response_topic = format!("rust/response/{}/energy_consume", requesting_client_id);
            if let Some(consume) = json_value.get("data").and_then(Value::as_f64) {
                match get_nodes_with_energy_consume(consume, &write_conn).await {
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

        Some("newestids") => {
            info!("Processing 'newestids' request for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/newestids", requesting_client_id);
            match get_newest_ids(&write_conn).await {
                Ok(nodes) => { 
                    publish_result(client, &response_topic, &nodes).await?;
                },
                Err(e) => { 
                    error!("Failed to get newest IDs for Client-ID: {}: {}", requesting_client_id, e);
                    return publish_error_response(client, &requesting_client_id, "newestids", &format!("Failed to get newest IDs: {}", e)).await;
                }
            }
        },
        
        Some("newestsensordata") => {
            info!("Processing 'newestsensordata' request for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/newestsensordata", requesting_client_id);
            match get_newest_sensordata(&write_conn).await {
                Ok(nodes) => { 
                    publish_result(client, &response_topic, &nodes).await?;
                },
                Err(e) => { 
                    error!("Failed to get newest sensor data for Client-ID: {}: {}", requesting_client_id, e);
                    return publish_error_response(client, &requesting_client_id, "newestsensordata", &format!("Failed to get newest sensor data: {}", e)).await;
                }
            }
        },
        
        Some("newestenergydata") => {
            info!("Processing 'newestenergydata' request for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/newestenergydata", requesting_client_id);
            match get_newest_energydata(&write_conn).await {
                Ok(nodes) => { 
                    publish_result(client, &response_topic, &nodes).await?;
                },
                Err(e) => { 
                    error!("Failed to get newest energy data for Client-ID: {}: {}", requesting_client_id, e);
                    return publish_error_response(client, &requesting_client_id, "newestenergydata", &format!("Failed to get newest energy data: {}", e)).await;
                }
            }
        },

        Some("addrobotdata") => {
            info!("Processing 'add' robotdata for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/add/robotdata", requesting_client_id);
            if let Some(add_data) = json_value.get("data") { 
                match create_new_nodes(add_data, &write_conn).await {
                    Ok(uuid_id_pairs) => {
                        let count = uuid_id_pairs.len();
                        if count > 0 {
                            
                            let livedata_topic = "rust/response/livedata";
                            let livedata = json!({
                                "type": "robotdata",
                                "source": "mqtt",
                                "client_id": requesting_client_id,
                                "timestamp": chrono::Utc::now().to_rfc3339(),
                                "count": count,
                                "ids": uuid_id_pairs.iter()
                                    .map(|(uuid, id)| json!({"uuid": uuid, "id": id}))
                                    .collect::<Vec<_>>(),
                                "data": add_data
                            });
                            
                           
                            if let Err(e) = publish_result(client, livedata_topic, &livedata).await {
                                warn!("Failed to publish robotdata to livedata topic: {}", e);
                            } else {
                                info!("Published robotdata to livedata topic");
                            }
                            
                            let response = json!({
                                "status": "success",
                                "message": format!("Successfully processed {} nodes/relations", count),
                                "count": count
                            });
                            publish_result(client, &response_topic, &response).await?;
                        } else {
                            info!("No new nodes created or relations added (data might already exist or update occurred). Client-ID: {}", requesting_client_id);
                            let response = json!({
                                "status": "no_change", 
                                "message": "No new nodes or relations were created (data might already exist or represent an update)",
                                "count": 0
                            });
                            publish_result(client, &response_topic, &response).await?;
                        }
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
        
        Some("addenergydata") => {
            info!("Processing 'add' energydata for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/add/energydata", requesting_client_id);
            if let Some(add_data) = json_value.get("data") { 
                match create_new_energy_nodes(add_data, &write_conn).await {
                    Ok(count) => {
                        if count > 0 {
                            
                            let livedata_topic = "rust/response/livedata";
                            let livedata = json!({
                                "type": "energydata",
                                "source": "mqtt",
                                "client_id": requesting_client_id,
                                "timestamp": chrono::Utc::now().to_rfc3339(),
                                "count": count,
                                "data": add_data
                            });
                            
                            
                            if let Err(e) = publish_result(client, livedata_topic, &livedata).await {
                                warn!("Failed to publish energydata to livedata topic: {}", e);
                            } else {
                                info!("Published energydata to livedata topic");
                            }
                            
                            let response = json!({
                                "status": "success",
                                "message": format!("Successfully processed {} energy nodes", count),
                                "count": count
                            });
                            publish_result(client, &response_topic, &response).await?;
                        } else {
                            info!("No new energy nodes created (data might already exist or update occurred). Client-ID: {}", requesting_client_id);
                            let response = json!({
                                "status": "no_change", 
                                "message": "No new energy nodes were created (data might already exist or represent an update)",
                                "count": 0
                            });
                            publish_result(client, &response_topic, &response).await?;
                        }
                    },
                    Err(err) => {
                        error!("Failed to add/update energy nodes for Client-ID: {}. Error: {}", requesting_client_id, err);
                        return publish_error_response(client, &requesting_client_id, "add", &format!("Failed to process add energy data request: {}", err)).await;
                    }
                }
            } else {
                warn!("Missing 'data' field for 'add' energydata request. Client: {}", requesting_client_id);
                return publish_error_response(client, &requesting_client_id, "add", "Missing 'data' field").await;
            }
        },
        
        Some("addsensordata") => {
            info!("Processing 'add' sensordata for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/add/sensordata", requesting_client_id);
            if let Some(add_data) = json_value.get("data") { 
                match create_new_sensor_nodes(add_data, &write_conn).await {
                    Ok(count) => {
                        if count > 0 {
                            
                            let livedata_topic = "rust/response/livedata";
                            let livedata = json!({
                                "type": "sensordata",
                                "source": "mqtt",
                                "client_id": requesting_client_id,
                                "timestamp": chrono::Utc::now().to_rfc3339(),
                                "count": count,
                                "data": add_data
                            });
                            
                            
                            if let Err(e) = publish_result(client, livedata_topic, &livedata).await {
                                warn!("Failed to publish sensordata to livedata topic: {}", e);
                            } else {
                                info!("Published sensordata to livedata topic");
                            }
                            
                            let response = json!({
                                "status": "success",
                                "message": format!("Successfully processed {} sensor nodes", count),
                                "count": count
                            });
                            publish_result(client, &response_topic, &response).await?;
                        } else {
                            info!("No new sensor nodes created (data might already exist or update occurred). Client-ID: {}", requesting_client_id);
                            let response = json!({
                                "status": "no_change", 
                                "message": "No new sensor nodes were created (data might already exist or represent an update)",
                                "count": 0
                            });
                            publish_result(client, &response_topic, &response).await?;
                        }
                    },
                    Err(err) => {
                        error!("Failed to add/update sensor nodes for Client-ID: {}. Error: {}", requesting_client_id, err);
                        return publish_error_response(client, &requesting_client_id, "add", &format!("Failed to process add sensor data request: {}", err)).await;
                    }
                }
            } else {
                warn!("Missing 'data' field for 'add' sensordata request. Client: {}", requesting_client_id);
                return publish_error_response(client, &requesting_client_id, "add", "Missing 'data' field").await;
            }
        },

        Some("relation") => {
            info!("Processing 'relation' data export for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/relation", requesting_client_id);
           
            match export_all_with_relationships(&write_conn, Some(1000)).await { 
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
                match get_paginated_ids(page_number, &write_conn).await {
                    Ok(nodes) => {
                        publish_result(client, &response_topic, &nodes).await?;
                    },
                    Err(e) => {
                        error!("Failed to get paginated data (page {}) for Client-ID: {}: {}", page_number, requesting_client_id, e);
                        return publish_error_response(client, &requesting_client_id, "page", &format!("Failed to get paginated data: {}", e)).await;
                    }
                }
            } else {
                warn!("Missing or invalid 'data' field for 'page' request. Client: {}", requesting_client_id);
                return publish_error_response(client, &requesting_client_id, "page", "Missing or invalid 'data' field (must be a positive integer page number)").await;
            }
        },

        Some("delete") => {
            info!("Processing 'delete' data for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/delete", requesting_client_id);
        
            if let Some(data_value) = json_value.get("data") {
                if let Some(id_array) = data_value.as_array() {
                    
                    let ids_to_delete: Vec<i64> = id_array.iter()
                        .filter_map(|v| v.as_i64())
                        .collect();
        
                    if ids_to_delete.is_empty() && !id_array.is_empty() {
                         warn!("'data' array for 'delete' request contained no valid numeric IDs. Client: {}", requesting_client_id);
                         return publish_error_response(client, &requesting_client_id, "delete", "'data' array must contain numeric IDs").await;
                    }
                     if ids_to_delete.is_empty() && id_array.is_empty() {
                         info!("Received empty 'data' array for 'delete' request. No action taken. Client: {}", requesting_client_id);
        
                         let response = json!({
                             "status": "success",
                             "message": "Received empty list, no nodes deleted.",
                             "deleted_count": 0
                         });
                         publish_result(client, &response_topic, &response).await?;
                         
                     } else {
                       
                        match delete_data_by_id(&ids_to_delete, &write_conn).await {
                            Ok(deleted_count) => {
                                if deleted_count > 0 {
                                    info!("Successfully deleted {} nodes for Client-ID: {}", deleted_count, requesting_client_id);
                                    let response = json!({
                                        "status": "success",
                                        "message": format!("Successfully deleted {} node(s).", deleted_count),
                                        "deleted_count": deleted_count
                                    });
                                    publish_result(client, &response_topic, &response).await?;
                                } else {
                                    warn!("No nodes found matching the provided IDs for deletion. Client-ID: {}", requesting_client_id);
                                    let response = json!({
                                        "status": "not_found", 
                                        "message": "No nodes found matching the provided IDs.",
                                        "deleted_count": 0
                                    });
                                    publish_result(client, &response_topic, &response).await?;
                                }
                            },
                            Err(err) => {
                                error!("Failed to delete nodes for Client-ID: {}. Error: {}", requesting_client_id, err);
                                return publish_error_response(client, &requesting_client_id, "delete", &format!("Failed to process delete request: {}", err)).await;
                            }
                        }
                    }
                } else {
                    warn!("Invalid 'data' field format for 'delete' request (must be an array of numeric IDs). Client: {}", requesting_client_id);
                    return publish_error_response(client, &requesting_client_id, "delete", "Invalid 'data' field format (must be an array of numeric IDs)").await;
                }
            } else {
                 warn!("Missing 'data' field for 'delete' request. Client: {}", requesting_client_id);
                return publish_error_response(client, &requesting_client_id, "delete", "Missing 'data' field").await;
            }
        },

        Some("cheap_energy") => {
            info!("Processing 'cheap_energy' request for Client-ID: {}", requesting_client_id);
            let response_topic = format!("rust/response/{}/cheap_energy", requesting_client_id);
            let start = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
            let end = (Local::now() + Duration::hours(24)).format("%Y-%m-%d %H:%M:%S").to_string();

                let (start_time, end_time) = (start, end);
                match get_cheap_energy(&start_time, &end_time, &write_conn).await {
                    Some(nodes) => {
                        publish_result(client, &response_topic, &nodes).await?;
                    },
                    None => {
                        error!("Failed to get cheap energy data for Client-ID: {} in range ('{}' - '{}')", requesting_client_id, start_time, end_time);
                        return publish_error_response(client, &requesting_client_id, "cheap_energy", "Failed to get cheap energy data").await;
                    }
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
          
             let _response_topic = format!("rust/response/{}", requesting_client_id);
             return publish_error_response(client, &requesting_client_id, "unknown", "Missing 'request' field in payload").await;
            
        }
    }

    Ok(())
}