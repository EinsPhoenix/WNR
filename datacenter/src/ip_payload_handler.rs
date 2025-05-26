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
use crate::webrtc_server::WebRtcServer;

pub async fn process_json(
    json: &Value, 
    db_handler: Arc<db::DatabaseCluster>, 
    socket: &mut TcpStream,
    mqtt_client: Option<&Arc<AsyncClient>>,
    webrtc_server: Option<&Arc<WebRtcServer>> 
) -> Result<(), String> {
  
    
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
            Some("videostream") => { 
                let result = handle_videostream_data(json, webrtc_server).await;
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

async fn handle_videostream_data(
    json: &Value,
    webrtc_server: Option<&Arc<WebRtcServer>>
) -> Result<String, String> {
    let server = match webrtc_server {
        Some(s) => s,
        None => {
            
            return Ok("Video stream data received, WebRTC server not available".to_string());
        }
    };

    let client_count = server.get_client_count().await;
    if client_count == 0 {
        return Ok("Video stream ignored, no WebRTC clients connected".to_string());
    }

    if let Some(video_data_val) = json.get("data") {
        if let Some(video_data_array) = video_data_val.as_array() {
            let mut total_frames_processed = 0;
            
            
            for (frame_index, frame_val) in video_data_array.iter().enumerate() {
                if let Some(frame_data_str) = frame_val.as_str() {
                    match server.broadcast_video_chunks(frame_data_str, frame_index).await {
                        Ok(_) => {
                            total_frames_processed += 1;
                           
                        }
                        Err(e) => {
                            warn!("Failed to send frame {} to WebRTC clients: {}", frame_index, e);
                        }
                    }

                    if frame_index < video_data_array.len() - 1 {
                        tokio::time::sleep(tokio::time::Duration::from_millis(10)).await;
                    }
                } else {
                    warn!("Frame {} is not a valid string", frame_index);
                }
            }
            
            Ok(format!("Processed {} video frames successfully, sent to {} clients", total_frames_processed, client_count))
        } else if let Some(video_data_str) = video_data_val.as_str() {
            
            
            match server.broadcast_video_chunks(video_data_str, 0).await {
                Ok(_) => {
                    info!("Successfully sent single video frame to {} WebRTC clients", client_count);
                    Ok(format!("Video frame sent successfully to {} clients", client_count))
                }
                Err(e) => {
                    warn!("Failed to send video frame to WebRTC clients: {}", e);
                    Err(format!("Failed to send video frame to WebRTC clients: {}", e))
                }
            }
        } else {
            Err("Field 'data' in 'videostream' JSON is neither a string nor an array".to_string())
        }
    } else {
        Err("No 'data' field found in 'videostream' JSON".to_string())
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
    let json_string = json.to_string();
    let response = format!("{}\n", json_string);
    
    match socket.write_all(response.as_bytes()).await {
        Ok(_) => {
            
            match socket.flush().await {
                Ok(_) => {
                    
                    tokio::time::sleep(tokio::time::Duration::from_millis(1)).await;
                    Ok(())
                }
                Err(e) => Err(format!("Error flushing response: {}", e))
            }
        },
        Err(e) => Err(format!("Error sending response: {}", e)),
    }
}