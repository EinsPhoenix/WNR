use log::{info, warn};
use serde_json::{Value, json};
use std::sync::Arc;
use tokio::io::AsyncWriteExt;
use tokio::net::TcpStream;
use rumqttc::AsyncClient;

use crate::db;
use crate::db_operations::sharding::*;
use crate::command_handler::router;
use crate::mqtt::publisher::publish_result;

pub async fn process_json(
    json: &Value, 
    db_handler: Arc<db::DatabaseCluster>, 
    socket: &mut TcpStream,
    mqtt_client: Option<&Arc<AsyncClient>>
) -> Result<(), String> {
    info!("Processing JSON: {}", json);
    
    if let Some(message_type) = json.get("type") {
        match message_type.as_str() {
            Some("message") => {
                let result = handle_message(json);
                send_response(socket, &result).await?;
                Ok(())
            },
            Some("command") => {
                let result = handle_command(json, db_handler).await;
                send_response(socket, &result).await?;
                Ok(())
            },
            Some("robotdata") => {
                let result = handle_robotdata(json, db_handler, mqtt_client).await;
                let response_to_log = match &result {
                    Ok(msg) => json!({ "status": "success", "message": msg }),
                    Err(err) => json!({ "status": "error", "message": err }),
                };
                info!("Sending response to TCP client for robotdata: {}", response_to_log);
                send_response(socket, &result).await?;
                Ok(())
            },
            Some("energydata") => {
                let result = handle_energydata(json, db_handler, mqtt_client).await;
                send_response(socket, &result).await?;
                Ok(())
            },
            Some("sensordata") => {
                let result = handle_sensordata(json, db_handler, mqtt_client).await;
                send_response(socket, &result).await?;
                Ok(())
            },
            _ => {
                let error_msg = format!("Unknown message type: {:?}", message_type);
                send_error(socket, &error_msg).await?;
                Err(error_msg)
            }
        }
    } else {
        let error_msg = "JSON has no type field".to_string();
        send_error(socket, &error_msg).await?;
        Err(error_msg)
    }
}

fn handle_message(json: &Value) -> Result<String, String> {
    if let Some(content) = json.get("content") {
        info!("Received message: {:?}", content);
        Ok(format!("Message processed: {}", content))
    } else {
        Err("No 'content' field found in message".to_string())
    }
}

async fn handle_command(json: &Value, db_handler: Arc<db::DatabaseCluster>) -> Result<String, String> {
    if let Some(command) = json.get("command") {
        info!("Received command: {:?}", command);
        
        if let Some(cmd_str) = command.as_str() {
            match router(cmd_str, db_handler).await {
                Ok(true) => Ok(format!("Command '{}' executed successfully", cmd_str)),
                Ok(false) => Err(format!("Command '{}' execution failed", cmd_str)),
                Err(e) => Err(format!("Error processing command '{}': {}", cmd_str, e)),
            }
        } else {
            Err(format!("Command is not a string: {:?}", command))
        }
    } else {
        Err("No 'command' field found in JSON".to_string())
    }
}

async fn handle_robotdata(
    json: &Value, 
    db_handler: Arc<db::DatabaseCluster>,
    mqtt_client: Option<&Arc<AsyncClient>>
) -> Result<String, String> {
    if let Some(data) = json.get("data") {
        let primary_conn = db_handler.get_main_db().await;
      
        match create_new_nodes(data, &primary_conn).await {
            Ok(0) => {
                Ok("No new nodes created (data might be empty or nodes already exist)".to_string())
            },
            Ok(count) => {
              
                if let Some(client) = mqtt_client {
                    let response_topic = "rust/response/livedata";
                    let livedata = json!({
                        "type": "robotdata",
                        "source": "tcp",
                        "timestamp": chrono::Utc::now().to_rfc3339(),
                        "count": count,
                        "data": data
                    });

                  
                    if let Err(e) = publish_result(client, response_topic, &livedata).await {
                        warn!("Failed to publish robotdata to livedata topic: {}", e);
                    } else {
                        info!("Published robotdata to livedata topic");
                    }
                }
                
                Ok(format!("{} nodes created successfully", count))
            }, 
            Err(error_msg) => Err(error_msg),
        }
    } else {
        Err("No 'data' field found in JSON".to_string())
    }
}

async fn handle_energydata(
    json: &Value, 
    db_handler: Arc<db::DatabaseCluster>,
    mqtt_client: Option<&Arc<AsyncClient>>
) -> Result<String, String> {
    if let Some(data) = json.get("data") {
        let primary_conn = db_handler.get_main_db().await;
        
        match create_new_energy_nodes(data, &primary_conn).await {
            Ok(0) => {
                Ok("No new nodes created (data might be empty or nodes already exist)".to_string())
            },
            Ok(count) => {
               
                if let Some(client) = mqtt_client {
                    let response_topic = "rust/response/livedata";
                    let livedata = json!({
                        "type": "energydata",
                        "source": "tcp",
                        "timestamp": chrono::Utc::now().to_rfc3339(),
                        "count": count,
                        "data": data
                    });

                  
                    if let Err(e) = publish_result(client, response_topic, &livedata).await {
                        warn!("Failed to publish energydata to livedata topic: {}", e);
                    } else {
                        info!("Published energydata to livedata topic");
                    }
                }
                
                Ok(format!("{} nodes created successfully", count))
            }, 
            Err(error_msg) => Err(error_msg),
        }
    } else {
        Err("No 'data' field found in JSON".to_string())
    }
}

async fn handle_sensordata(
    json: &Value, 
    db_handler: Arc<db::DatabaseCluster>,
    mqtt_client: Option<&Arc<AsyncClient>>
) -> Result<String, String> {
    if let Some(data) = json.get("data") {
        let primary_conn = db_handler.get_main_db().await;
        
        match create_new_sensor_nodes(data, &primary_conn).await {
            Ok(0) => {
                Ok("No new nodes created (data might be empty or nodes already exist)".to_string())
            },
            Ok(count) => {
              
                if let Some(client) = mqtt_client {
                    let response_topic = "rust/response/livedata";
                    let livedata = json!({
                        "type": "sensordata",
                        "source": "tcp",
                        "timestamp": chrono::Utc::now().to_rfc3339(),
                        "count": count,
                        "data": data
                    });

                    // Publish but don't fail if MQTT publishing fails
                    if let Err(e) = publish_result(client, response_topic, &livedata).await {
                        warn!("Failed to publish sensordata to livedata topic: {}", e);
                    } else {
                        info!("Published sensordata to livedata topic");
                    }
                }
                
                Ok(format!("{} nodes created successfully", count))
            },
            Err(error_msg) => Err(error_msg),
        }
    } else {
        Err("No 'data' field found in JSON".to_string())
    }
}

async fn send_response(socket: &mut TcpStream, result: &Result<String, String>) -> Result<(), String> {
    let response = match result {
        Ok(msg) => json!({ "status": "success", "message": msg }),
        Err(err) => json!({ "status": "error", "message": err }),
    };
    
    send_json_response(socket, &response).await
}

async fn send_error(socket: &mut TcpStream, error_msg: &str) -> Result<(), String> {
    let response = json!({
        "status": "error",
        "message": error_msg
    });
    
    send_json_response(socket, &response).await
}

async fn send_json_response(socket: &mut TcpStream, json: &Value) -> Result<(), String> {
    info!("Sending response to TCP client: {}", json);
    match socket.write_all(json.to_string().as_bytes()).await {
        Ok(_) => {
            Ok(())
        },
        Err(e) => Err(format!("Error sending response: {}", e)),
    }
}