use rumqttc::{MqttOptions, AsyncClient, Event, Incoming, QoS, EventLoop};
use tokio::time::{self, Duration};
use log::{info, error, warn};
use serde_json::json;
use std::env;
use std::error::Error;
use uuid::Uuid;
use std::sync::Arc;
use chrono;

use crate::db;
use super::request_processor::process_request; 

// Function to establish connection with retry logic
async fn connect_with_retry(options: MqttOptions, buffer_size: usize) -> Result<(Arc<AsyncClient>, EventLoop), Box<dyn Error>> {
    let mut attempts = 0;
    let max_attempts = 5; 
    let retry_delay = Duration::from_secs(5);

    loop {
        attempts += 1;
        info!("Attempting MQTT connection (Attempt {}/{}) to {}:{}...", attempts, max_attempts, options.broker_address().0, options.broker_address().1);
        let (client, eventloop) = AsyncClient::new(options.clone(), buffer_size);
        let client_arc = Arc::new(client);
        let mut eventloop_clone = eventloop; 

      
        let connect_timeout = Duration::from_secs(20);
        match time::timeout(connect_timeout, async {
            loop {
                match eventloop_clone.poll().await {
                    Ok(Event::Incoming(Incoming::ConnAck(ack))) => {
                        if ack.code == rumqttc::ConnectReturnCode::Success {
                            info!("✅ MQTT connection successful: {:?}", ack);
                            return Ok((client_arc.clone(), eventloop_clone)); 
                        } else {
                            error!("❌ MQTT connection failed with code: {:?}", ack.code);
                            return Err(format!("Connection failed: {:?}", ack.code).into());
                        }
                    },
                    Ok(event) => warn!("Received unexpected event during connection: {:?}", event), 
                    Err(e) => {
                        error!("❌ Error polling event loop during connection: {}", e);
                        return Err(Box::new(e) as Box<dyn Error>);
                    }
                }
            }
        }).await {
            Ok(Ok((client, final_eventloop))) => return Ok((client, final_eventloop)), 
            Ok(Err(e)) => { // Connection failed 
                 error!("MQTT connection attempt {} failed: {}", attempts, e);
                 if attempts >= max_attempts {
                     return Err(e); // Max attempts reached
                 }
                 info!("Retrying connection in {:?}...", retry_delay);
                 time::sleep(retry_delay).await;
            }
            Err(_) => { // Timeout
                error!("⌛ MQTT connection attempt {} timed out after {:?}.", attempts, connect_timeout);
                if attempts >= max_attempts {
                    return Err("Connection timed out after multiple retries".into());
                }
                info!("Retrying connection in {:?}...", retry_delay);
                time::sleep(retry_delay).await;
            }
        }
    }
}


pub async fn start_mqtt_client(db_handler: Arc<db::DatabaseCluster>) -> Result<(), Box<dyn Error>> {
    let client_id = format!("rust-mqtt-server-{}", Uuid::new_v4());
    info!("Initializing MQTT client with ID: {}", client_id);

    let broker_host = env::var("MQTT_BROKER").unwrap_or_else(|_| "mosquitto-broker".into());
    let broker_port = env::var("MQTT_PORT").unwrap_or_else(|_| "1883".into()).parse::<u16>().unwrap_or(1883);

    let mut mqtt_options = MqttOptions::new(&client_id, broker_host, broker_port);
    mqtt_options.set_keep_alive(Duration::from_secs(60));
    mqtt_options.set_clean_session(true); 
    mqtt_options.set_credentials(
        env::var("MQTT_USER").unwrap_or_else(|_| "admin".into()),
        env::var("MQTT_PASSWORD").unwrap_or_else(|_| "admin".into())
    );
    

  
    let (client, mut eventloop) = connect_with_retry(mqtt_options, 10).await?; 

    info!("🚀 MQTT Client Connected. Starting service...");

    // Subscribe request topic
    let subscribe_topic = "rust/request";
    match client.subscribe(subscribe_topic, QoS::AtLeastOnce).await {
         Ok(_) => info!("🔔 Subscribed successfully to: {}", subscribe_topic),
         Err(e) => {
             error!("❌ Failed to subscribe to {}: {}", subscribe_topic, e);
             return Err(e.into()); 
         }
    }


    // Heartbeat Task
    let heartbeat_client = client.clone();
    let heartbeat_client_id = client_id.clone();
    tokio::spawn(async move {
        let mut interval = time::interval(Duration::from_secs(60));
        let status_topic = "rust/status";
        loop {
            interval.tick().await;
            let status = json!({
                "server_id": heartbeat_client_id,
                "status": "running",
                "timestamp": chrono::Utc::now().to_rfc3339()
            });

            match serde_json::to_string(&status) {
                Ok(payload_str) => {
                    if let Err(e) = heartbeat_client.publish(
                        status_topic,
                        QoS::AtLeastOnce,
                        false, 
                        payload_str
                    ).await {
                        error!("❌ Failed to send heartbeat to {}: {}", status_topic, e);
                        
                    } else {
                         info!("💓 Heartbeat sent to {}", status_topic);
                    }
                },
                Err(e) => {
                    error!("❌ Failed to serialize heartbeat status: {}", e);
                }
            }
        }
    });

    // Main processing messages
    info!("👂 Waiting for requests on {}...", subscribe_topic);
    loop {
        match eventloop.poll().await {
            Ok(Event::Incoming(Incoming::Publish(msg))) => {
                if msg.topic == subscribe_topic {
                    info!("Received message on {}", subscribe_topic);
                    let process_client = client.clone();
                    let payload = msg.payload.to_vec(); 
                    let db_handler_clone = Arc::clone(&db_handler);

                   
                    tokio::spawn(async move {
                        if let Err(e) = process_request(&process_client, &payload, &db_handler_clone).await {
                           
                             error!("Task processing request failed: {}", e);
                        }
                    });
                } else {
                    warn!("Received message on unexpected topic: {}", msg.topic);
                }
            },
            Ok(Event::Incoming(Incoming::Disconnect)) => {
                warn!("🔌 MQTT client disconnected. The event loop will terminate.");
                
                return Err("MQTT client disconnected".into());
            },
             Ok(Event::Incoming(Incoming::PingResp)) => {
                info!("Received PingResp");
             },
             Ok(Event::Outgoing(outgoing)) => {
                 info!("MQTT Outgoing: {:?}", outgoing);
             }
            Ok(event) => {
                
                 info!("Received other MQTT event: {:?}", event);
            },
            Err(e) => {
                error!("❌ Error in MQTT event loop: {}. Attempting to continue...", e);
                time::sleep(Duration::from_secs(5)).await;

               
                if matches!(e, rumqttc::ConnectionError::Io(_)) || matches!(e, rumqttc::ConnectionError::MqttState(_)) {
                     error!("Persistent connection error detected ({:?}). Terminating event loop.", e);
                     return Err(Box::new(e)); 
                }
               
            }
        }
    }
    
}