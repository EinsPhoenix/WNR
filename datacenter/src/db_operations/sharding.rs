use neo4rs::{Graph, query};
use log::{error, info, warn};
use serde_json::Value;
use std::collections::HashMap;
use super::cypher_queries::*;
// use super::logfunctions::log_benchmark;

// Validates if a new item has all required fields for insertion.
// Input: item - a JSON object representing the item.
// Returns: bool - true if valid, false otherwise.
async fn validate_new_item(item: &Value) -> bool {
            item.get("uuid").and_then(|v| v.as_str()).is_some()
        && item.get("color").and_then(|v| v.as_str()).is_some()
        && item.get("sensor_data").map(|v| v.is_object()).unwrap_or(false)
        && item.get("sensor_data").and_then(|sd| sd.get("temperature")).and_then(|t| t.as_f64()).is_some()
        && item.get("sensor_data").and_then(|sd| sd.get("humidity")).and_then(|h| h.as_f64()).is_some()
        && item.get("timestamp").and_then(|v| v.as_str()).is_some()
        && item.get("energy_consume").and_then(|v| v.as_f64()).is_some()
        && item.get("energy_cost").and_then(|v| v.as_f64()).is_some()
}

// Prepares parameters for a new item to be inserted into the database.
// Input: item - a JSON object representing the item.
// Returns: Option<HashMap<String, String>> - prepared parameters or None if invalid.
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

// Validates if a new sensor data entry has all required fields for insertion.
// Input: item - a JSON object representing the sensor data.
// Returns: bool - true if valid, false otherwise.
async fn validate_new_sensordata(item: &Value) -> bool {
    item.get("timestamp").and_then(|v| v.as_str()).is_some()
        && item.get("temperature").and_then(|v| v.as_f64()).is_some()
        && item.get("humidity").and_then(|v| v.as_f64()).is_some()
}

// Prepares parameters for a new sensor data entry to be inserted into the database.
// Input: item - a JSON object representing the sensor data.
// Returns: Option<HashMap<String, String>> - prepared parameters or None if invalid.
async fn prepare_new_sensordata(item: &Value) -> Option<HashMap<String, String>> {
    let mut params = HashMap::new();

    params.insert("timestamp".to_string(), item.get("timestamp")?.as_str()?.to_string());
    params.insert("temperature".to_string(), item.get("temperature")?.as_f64()?.to_string());
    params.insert("humidity".to_string(), item.get("humidity")?.as_f64()?.to_string());

    Some(params)
}

// Validates if a new energy data entry has all required fields for insertion.
// Input: item - a JSON object representing the energy data.
// Returns: bool - true if valid, false otherwise.
async fn validate_new_energydata(item: &Value) -> bool {
    item.get("timestamp").and_then(|v| v.as_str()).is_some()
        && item.get("energy_cost").and_then(|v| v.as_f64()).is_some()
}

// Prepares parameters for a new energy data entry to be inserted into the database.
// Input: item - a JSON object representing the energy data.
// Returns: Option<HashMap<String, String>> - prepared parameters or None if invalid.
async fn prepare_new_energydata(item: &Value) -> Option<HashMap<String, String>> {
    let mut params = HashMap::new();

    params.insert("timestamp".to_string(), item.get("timestamp")?.as_str()?.to_string());
    params.insert("energy_cost".to_string(), item.get("energy_cost")?.as_f64()?.to_string());

    Some(params)
}

// Validates and retrieves a JSON array from the input data.
// Input: data - a JSON object to validate.
// Returns: Result<&Vec<Value>, String> - the JSON array or an error message.
async fn validate_and_get_data_array(data: &Value) -> Result<&Vec<Value>, String> {
    match data.as_array() {
        Some(arr) => Ok(arr),
        None => Err("Input data is not a valid JSON array".to_string()),
    }
}

// Retrieves the current maximum ID from the database and increments it by a specified value.
// Input: &Graph - a reference to the Neo4j graph instance, increment - the value to increment the ID by.
// Returns: Result<i64, String> - the previous maximum ID or an error message.
pub async fn get_current_max_id(graph: &Graph, increment: i64) -> Result<i64, String> {
    if increment <= 0 {
        return Ok(0);
    }

    let query_str = "USE fabric.dbshard1
                    MERGE (counter:GlobalIdCounter)
                    ON CREATE SET counter.value = 0
                    WITH counter
                    SET counter.value = counter.value + $increment
                    RETURN counter.value - $increment AS previous_max_id";

    info!("Fetching and incrementing current max ID by {} from Shard 1", increment);
    match graph.execute(query(query_str).param("increment", increment)).await {
        Ok(mut result) => {
            match result.next().await {
                Ok(Some(row)) => {
                    let prev_max_id: i64 = row.get("previous_max_id").map_err(|e| format!("Failed to parse previous_max_id: {}", e))?;
                    Ok(prev_max_id)
                },
                Ok(None) => {
                    warn!("No max ID found (likely first increment), starting from 0.");
                    Ok(0)
                },
                Err(e) => {
                    let err_msg = format!("Error fetching max ID result row: {}", e);
                    error!("{}", err_msg);
                    Err(err_msg)
                }
            }
        },
        Err(e) => {
            let err_msg = format!("Failed to execute max ID query: {}", e);
            error!("{}", err_msg);
            Err(err_msg)
        }
    }
}

// Creates new nodes in the database across all shards using the provided data.
// Input: data - a JSON array of items to insert, &Graph - a reference to the Neo4j graph instance.
// Returns: Result<usize, String> - the number of successfully created nodes or an error message.
pub async fn create_new_nodes(data: &Value, graph: &Graph) -> Result<usize, String> {
    let start_time = std::time::Instant::now();
    info!("Starting batch data insertion process");

    let data_array = match validate_and_get_data_array(data).await {
        Ok(arr) => arr,
        Err(e) => return Err(format!("Input validation failed: {}", e)),
    };

    let total_items = data_array.len();
    if total_items == 0 {
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

    let initial_max_id = match get_current_max_id(graph, total_items as i64).await {
        Ok(id) => id,
        Err(e) => return Err(format!("Failed to get starting ID block: {}", e)),
    };
    let mut current_id_counter = initial_max_id + 1;
    info!("Reserved ID block starting from: {}", current_id_counter);

    const BATCH_SIZE: usize = 8000;
    let mut processed_count = 0;
    let mut errors = Vec::new();

    for batch_start in (0..total_items).step_by(BATCH_SIZE) {
        let current_batch_actual_size = std::cmp::min(BATCH_SIZE, total_items - batch_start);
        // let batch_start_time = std::time::Instant::now();

        info!("Processing batch of {} items starting at index {}", current_batch_actual_size, batch_start);

        let mut batch_data = Vec::with_capacity(current_batch_actual_size);
        for i in 0..current_batch_actual_size {
            let item_index = batch_start + i;
            let item = &data_array[item_index];

            match prepare_all_item_params(item).await {
                Some(mut params) => {
                    let item_id = current_id_counter;
                    current_id_counter += 1;

                    params.insert("id".to_string(), item_id.to_string());

                    batch_data.push((
                        item_id,
                        params.get("uuid").unwrap().clone(),
                        params.get("color").unwrap().clone(),
                        params.get("temperature").unwrap().parse::<f64>().unwrap_or(0.0),
                        params.get("humidity").unwrap().parse::<f64>().unwrap_or(0.0),
                        params.get("timestamp").unwrap().clone(),
                        params.get("energy_consume").unwrap().parse::<f64>().unwrap_or(0.0),
                        params.get("energy_cost").unwrap().parse::<f64>().unwrap_or(0.0)
                    ));
                },
                None => {
                    let error_msg = format!("Failed to extract parameters for item at index {}", item_index);
                    error!("{}", error_msg);
                    errors.push(error_msg);
                    continue;
                }
            }
        }

        if batch_data.is_empty() {
            warn!("No valid items prepared in the current batch (indices {} to {}), skipping database operation...", batch_start, batch_start + current_batch_actual_size - 1);
            continue;
        }

        let shard1_batch_data = batch_data.iter()
            .map(|(id, uuid, color, _, _, _, _, _)| {
                let row_list: neo4rs::BoltList = vec![
                    (*id).into(),
                    uuid.clone().into(),
                    color.clone().into(),
                ].into();
                neo4rs::BoltType::List(row_list)
            })
            .collect::<Vec<neo4rs::BoltType>>();

        let shard2_batch_data = batch_data.iter()
            .map(|(id, _, _, temp, humidity, timestamp, _, _)| {
                let row_list: neo4rs::BoltList = vec![
                    (*id).into(),
                    (*id).into(),
                    (*id).into(),
                    (*temp).into(),
                    (*humidity).into(),
                    timestamp.clone().into(),
                ].into();
                neo4rs::BoltType::List(row_list)
            })
            .collect::<Vec<neo4rs::BoltType>>();

        let shard3_batch_data = batch_data.iter()
            .map(|(id, _, _, _, _, timestamp, energy_consume, energy_cost)| {
                let row_list: neo4rs::BoltList = vec![
                    (*id).into(),
                    (*id).into(),
                    (*id).into(),
                    (*id).into(),
                    (*id).into(),
                    timestamp.clone().into(),
                    (*energy_consume).into(),
                    (*energy_cost).into(),
                ].into();
                neo4rs::BoltType::List(row_list)
            })
            .collect::<Vec<neo4rs::BoltType>>();

        let params1 = query(CREATE_NODES_SHARD1).param("batch", shard1_batch_data);
        let params2 = query(CREATE_NODES_SHARD2).param("batch", shard2_batch_data);
        let params3 = query(CREATE_NODES_SHARD3).param("batch", shard3_batch_data);

        let shard1_fut = graph.execute(params1);
        let shard2_fut = graph.execute(params2);
        let shard3_fut = graph.execute(params3);

        let (res1, res2, res3) = tokio::join!(shard1_fut, shard2_fut, shard3_fut);

        let mut batch_success = true;
        match res1 {
            Ok(mut result) => {
                match result.next().await {
                    Ok(Some(row)) => {
                        match row.get::<i64>("nodes_created") {
                            Ok(count) => info!("Shard 1 batch successful: created {} nodes", count),
                            Err(e) => {
                                batch_success = false;
                                let error_msg = format!("Shard 1 batch failed to get node count: {}", e);
                                error!("{}", error_msg);
                                errors.push(error_msg);
                            }
                        }
                    },
                    Ok(None) => {
                        batch_success = false;
                        let error_msg = "Shard 1 batch query returned no results".to_string();
                        error!("{}", error_msg);
                        errors.push(error_msg);
                    },
                    Err(e) => {
                        batch_success = false;
                        let error_msg = format!("Error processing Shard 1 batch results: {}", e);
                        error!("{}", error_msg);
                        errors.push(error_msg);
                    }
                }
            },
            Err(e) => {
                batch_success = false;
                let error_msg = format!("Shard 1 task failed: {}", e);
                error!("{}", error_msg);
                errors.push(error_msg);
            }
        }

        match res2 {
            Ok(mut result) => {
                match result.next().await {
                    Ok(Some(row)) => {
                        match row.get::<i64>("nodes_created") {
                            Ok(count) => info!("Shard 2 batch successful: created {} nodes", count),
                            Err(e) => {
                                batch_success = false;
                                let error_msg = format!("Shard 2 batch failed to get node count: {}", e);
                                error!("{}", error_msg);
                                errors.push(error_msg);
                            }
                        }
                    },
                    Ok(None) => {
                        batch_success = false;
                        let error_msg = "Shard 2 batch query returned no results".to_string();
                        error!("{}", error_msg);
                        errors.push(error_msg);
                    },
                    Err(e) => {
                        batch_success = false;
                        let error_msg = format!("Error processing Shard 2 batch results: {}", e);
                        error!("{}", error_msg);
                        errors.push(error_msg);
                    }
                }
            },
            Err(e) => {
                batch_success = false;
                let error_msg = format!("Shard 2 task failed: {}", e);
                error!("{}", error_msg);
                errors.push(error_msg);
            }
        }

        match res3 {
            Ok(mut result) => {
                match result.next().await {
                    Ok(Some(row)) => {
                        match row.get::<i64>("nodes_created") {
                            Ok(count) => info!("Shard 3 batch successful: created {} nodes", count),
                            Err(e) => {
                                batch_success = false;
                                let error_msg = format!("Shard 3 batch failed to get node count: {}", e);
                                error!("{}", error_msg);
                                errors.push(error_msg);
                            }
                        }
                    },
                    Ok(None) => {
                        batch_success = false;
                        let error_msg = "Shard 3 batch query returned no results".to_string();
                        error!("{}", error_msg);
                        errors.push(error_msg);
                    },
                    Err(e) => {
                        batch_success = false;
                        let error_msg = format!("Error processing Shard 3 batch results: {}", e);
                        error!("{}", error_msg);
                        errors.push(error_msg);
                    }
                }
            },
            Err(e) => {
                batch_success = false;
                let error_msg = format!("Shard 3 task failed: {}", e);
                error!("{}", error_msg);
                errors.push(error_msg);
            }
        }

        if batch_success {
            processed_count += batch_data.len();
            // let batch_time = batch_start_time.elapsed();
            // let benchmark_result = log_benchmark(batch_data.len(), batch_time).await;
            // if let Err(e) = benchmark_result {
            //     warn!("Failed to log benchmark: {}", e);
            // }
            // info!("Batch completed: {}/{} records processed so far, batch time: {:.2?}, speed: {:.2} records/sec",
            //     processed_count, total_items, batch_time, batch_data.len() as f64 / batch_time.as_secs_f64());
        } else {
            warn!("Batch ending at index {} encountered errors, data consistency might be affected for {} items in this batch.", batch_start + current_batch_actual_size - 1, batch_data.len());
        }
    }

    let total_time = start_time.elapsed();
    info!("Data insertion completed: attempted to process {} records in {:.2?}", total_items, total_time);
    if processed_count > 0 && total_time.as_secs_f64() > 0.0 {
        info!("Average speed for successfully processed items: {:.2} records/second",
              processed_count as f64 / total_time.as_secs_f64());
    }

    if errors.is_empty() {
        if processed_count == total_items {
            Ok(processed_count)
        } else {
            let final_error_msg = format!(
                "Processed {} out of {} items successfully. Some items failed parameter preparation.",
                processed_count,
                total_items
            );
            warn!("{}", final_error_msg);
            Ok(processed_count)
        }
    } else {
        let combined_error = format!(
            "Attempted to process {} items. Successfully processed {} items. Encountered {} errors during database operations or parameter preparation: {}",
            total_items,
            processed_count,
            errors.len(),
            errors.join("; ")
        );
        error!("{}", combined_error);
        Ok(processed_count)
    }
}

// Creates new sensor data nodes in the database shard for sensor data.
// Input: data - a JSON array of sensor data entries, &Graph - a reference to the Neo4j graph instance.
// Returns: Result<usize, String> - the number of successfully created nodes or an error message.
pub async fn create_new_sensor_nodes(data: &Value, graph: &Graph) -> Result<usize, String> {
    let data_array = match validate_and_get_data_array(data).await {
        Ok(arr) => arr,
        Err(e) => return Err(format!("Input validation failed (expected array): {}", e)),
    };

    if data_array.is_empty() {
        info!("Received empty sensor data array. No nodes will be created.");
        return Ok(0);
    }

    for (index, item) in data_array.iter().enumerate() {
        if !validate_new_sensordata(item).await {
            let error_msg = format!("Invalid sensor data structure at index {}: Expected timestamp(string), temperature(float), humidity(float). Got: {:?}", index, item);
            error!("{}", error_msg);
            return Err(error_msg);
        }
    }

    let mut processed_count = 0;
    let mut errors = Vec::new();

    for (index, item) in data_array.iter().enumerate() {
        let params = match prepare_new_sensordata(item).await {
            Some(p) => p,
            None => {
                let error_msg = format!("Failed to extract parameters for sensor data at index {}: {:?}", index, item);
                error!("{}", error_msg);
                errors.push(error_msg);
                continue;
            }
        };

        let cypher = CREATE_SENSOR_NODES_SHARD2;
        let query = query(cypher).params(params.clone());

        let timestamp_str = params.get("timestamp").cloned().unwrap_or_else(|| "unknown".to_string());

        match graph.execute(query).await {
            Ok(mut result) => {
                match result.next().await {
                    Ok(Some(row)) => {
                        if row.get::<String>("timestamp").is_ok() {
                            info!("Successfully created sensor node with timestamp {}", timestamp_str);
                            processed_count += 1;
                        } else {
                            let error_msg = format!("Query executed for sensor data with timestamp {}, but failed to get confirmation timestamp from result.", timestamp_str);
                            error!("{}", error_msg);
                            errors.push(error_msg);
                        }
                    }
                    Ok(None) => {
                        let error_msg = format!("Query executed for sensor data with timestamp {}, but returned no confirmation row.", timestamp_str);
                        error!("{}", error_msg);
                        errors.push(error_msg);
                    }
                    Err(e) => {
                        let error_msg = format!("Failed to process result row for sensor data with timestamp {}: {}", timestamp_str, e);
                        error!("{}", error_msg);
                        errors.push(error_msg);
                    }
                }
            }
            Err(e) => {
                let error_msg = format!("Failed to execute query for sensor data with timestamp {}: {}", timestamp_str, e);
                error!("{}", error_msg);
                errors.push(error_msg);
            }
        }
    }

    if errors.is_empty() {
        info!(
            "Successfully processed all {} sensor data entries.",
            processed_count
        );
    } else {
        error!(
            "Processed {} out of {} sensor data entries. Encountered {} errors: {}",
            processed_count,
            data_array.len(),
            errors.len(),
            errors.join("; ")
        );
    }

    if !errors.is_empty() {
        Ok(processed_count)
    } else {
        Ok(processed_count)
    }
}

// Creates new energy data nodes in the database shard for energy data.
// Input: data - a JSON array of energy data entries, &Graph - a reference to the Neo4j graph instance.
// Returns: Result<usize, String> - the number of successfully created nodes or an error message.
pub async fn create_new_energy_nodes(data: &Value, graph: &Graph) -> Result<usize, String> {
    let data_array = match validate_and_get_data_array(data).await {
        Ok(arr) => arr,
        Err(e) => return Err(format!("Input validation failed (expected array): {}", e)),
    };

    if data_array.is_empty() {
        info!("Received empty energy data array. No nodes will be created.");
        return Ok(0);
    }

    for (index, item) in data_array.iter().enumerate() {
        if !validate_new_energydata(item).await {
            let error_msg = format!("Invalid energy data structure at index {}: Expected timestamp(string), energy_consume(float), energy_cost(float). Got: {:?}", index, item);
            error!("{}", error_msg);
            return Err(error_msg);
        }
    }

    let mut processed_count = 0;
    let mut errors = Vec::new();

    for (index, item) in data_array.iter().enumerate() {
        let params = match prepare_new_energydata(item).await {
            Some(p) => p,
            None => {
                let error_msg = format!("Failed to extract parameters for energy data at index {}: {:?}", index, item);
                error!("{}", error_msg);
                errors.push(error_msg);
                continue;
            }
        };

        let cypher = CREATE_ENERGY_COST_NODES_SHARD3;
        let query = query(cypher).params(params.clone());

        let timestamp_str = params.get("timestamp").cloned().unwrap_or_else(|| "unknown".to_string());

        match graph.execute(query).await {
            Ok(mut result) => {
                match result.next().await {
                    Ok(Some(row)) => {
                        if row.get::<String>("timestamp").is_ok() {
                            info!("Successfully created energy node with timestamp {}", timestamp_str);
                            processed_count += 1;
                        } else {
                            let error_msg = format!("Query executed for energy data with timestamp {}, but failed to get confirmation timestamp from result.", timestamp_str);
                            error!("{}", error_msg);
                            errors.push(error_msg);
                        }
                    }
                    Ok(None) => {
                        let error_msg = format!("Query executed for energy data with timestamp {}, but returned no confirmation row.", timestamp_str);
                        error!("{}", error_msg);
                        errors.push(error_msg);
                    }
                    Err(e) => {
                        let error_msg = format!("Failed to process result row for energy data with timestamp {}: {}", timestamp_str, e);
                        error!("{}", error_msg);
                        errors.push(error_msg);
                    }
                }
            }
            Err(e) => {
                let error_msg = format!("Failed to execute query for energy data with timestamp {}: {}", timestamp_str, e);
                error!("{}", error_msg);
                errors.push(error_msg);
            }
        }
    }

    if errors.is_empty() {
        info!(
            "Successfully processed all {} energy data entries.",
            processed_count
        );
    } else {
        error!(
            "Processed {} out of {} energy data entries. Encountered {} errors: {}",
            processed_count,
            data_array.len(),
            errors.len(),
            errors.join("; ")
        );
    }

    if !errors.is_empty() {
        Ok(processed_count)
    } else {
        Ok(processed_count)
    }
}