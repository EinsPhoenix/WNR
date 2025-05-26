use log::{info, error};
use dotenv::dotenv;
use webrtc_server::WebRtcServer;
use std::env;
use tokio::net::{TcpListener, TcpStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use std::io;
use serde_json::{json, Value};
use std::sync::Arc;
use rumqttc::AsyncClient; 
use fern::Dispatch;
use chrono::Local;
use std::thread;

mod db;
mod auth;
mod ip_payload_handler;
mod mqtt;
mod command_handler;
mod webrtc_server;

mod db_operations;

//log init
fn setup_logger() -> Result<(), fern::InitError> {
    Dispatch::new()
        .format(|out, message, record| {
            let timestamp = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();
            out.finish(format_args!(
                "[{}] [{}] {}",
                timestamp, record.level(), message
            ));
        })
        .level(log::LevelFilter::Info)
        .chain(std::io::stdout())
        .chain(fern::log_file("error.log")?)
        .apply()?;
    Ok(())
}

#[tokio::main]
async fn main() -> io::Result<()> {
    setup_logger().expect("Logger konnte nicht initialisiert werden!");
    dotenv().ok();

    info!("Starting the server...");

    let db_handler = db::get_database().await.map_err(|e| {
        error!("Failed to get database connection: {:?}", e);
        io::Error::new(io::ErrorKind::Other, "Database connection failed")
    })?;

    // Create a shared MQTT client that can be used by both the MQTT service and TCP handlers
    let mqtt_client = match mqtt::connection::create_mqtt_client().await {
        Ok(client) => {
            info!("Created shared MQTT client successfully");
            Some(Arc::clone(&client))
        },
        Err(e) => {
            error!("Failed to create shared MQTT client: {:?}", e);
            None
        }
    };

    let db_mqtt_handler_clone = Arc::clone(&db_handler);

    thread::spawn(move || {
        info!("Spawning dedicated thread for MQTT client...");
        let rt = match tokio::runtime::Runtime::new() {
            Ok(rt) => rt,
            Err(e) => {
                error!("Failed to create Tokio runtime for MQTT thread: {:?}", e);
                return;
            }
        };

        rt.block_on(async move {
            info!("MQTT client thread started. Running start_mqtt_client...");
            if let Err(e) = mqtt::connection::start_mqtt_client(db_mqtt_handler_clone).await {
                error!("MQTT client encountered an error: {:?}", e);
            }
            info!("MQTT client thread finished.");
        });
    });

    let password = env::var("SERVER_PASSWORD").expect("SERVER_PASSWORD not set in .env");
    let listener = TcpListener::bind("0.0.0.0:12345").await?;
    info!("Server is listening on 0.0.0.0:12345");

    let webrtc_server = Arc::new(WebRtcServer::new(1337));
    let webrtc_server_clone = Arc::clone(&webrtc_server);

    
    tokio::spawn(async move {
        if let Err(e) = webrtc_server_clone.start().await {
            error!("WebRTC server error: {}", e);
        }
    });

    loop {
        match listener.accept().await {
            Ok((socket, addr)) => {
                info!("New connection from: {}", addr);
                let password_clone = password.clone();
                let db_handler_clone = Arc::clone(&db_handler);
                let mqtt_client_clone = mqtt_client.clone();
                let webrtc_server_clone = Arc::clone(&webrtc_server);  
                
                tokio::spawn(async move {
                    if let Err(e) = handle_client(socket, password_clone, db_handler_clone, mqtt_client_clone, webrtc_server_clone).await {  
                        error!("Error handling client {}: {:?}", addr, e);
                    }
                });
            }
            Err(e) => error!("Failed to accept connection: {:?}", e),
        }
    }
}

async fn handle_client(
    mut socket: TcpStream,
    correct_password: String,
    db_handler: Arc<db::DatabaseCluster>,
    mqtt_client: Option<Arc<AsyncClient>>,
    webrtc_server: Arc<WebRtcServer>  
) -> io::Result<()> {
    if !auth::authenticate_client(&mut socket, &correct_password).await? {
        return Ok(());
    }

    loop {
        match receive_json(&mut socket).await {
            Ok(Some(json)) => {
                
                if let Err(e) = ip_payload_handler::process_json(&json, Arc::clone(&db_handler), &mut socket, mqtt_client.as_ref(), Some(&webrtc_server)).await {
                    error!("Error processing JSON: {}", e);
                }
            },
            Ok(None) => {
                info!("Client disconnected: {}", socket.peer_addr().map(|a| a.to_string()).unwrap_or_else(|_| "unknown".to_string()));
                break;
            },
            Err(e) => {
                error!("Error receiving JSON from {}: {:?}", socket.peer_addr().map(|a| a.to_string()).unwrap_or_else(|_| "unknown".to_string()), e);
                break;
            }
        }
    }

    Ok(())
}

async fn receive_json(socket: &mut TcpStream) -> io::Result<Option<Value>> {
    const MAX_JSON_SIZE: usize = 10 * 1024 * 1024;

    let mut buf = vec![0; MAX_JSON_SIZE];
    let n = socket.read(&mut buf).await?;

    if n == 0 {
        return Ok(None);
    }

    if n >= MAX_JSON_SIZE {
        let error_msg = "Error: JSON payload too large (exceeds 10MB limit)";
        error!("{}", error_msg);

        let error_response = json!({
            "status": "error",
            "message": error_msg
        });

        let _ = socket.write_all(error_response.to_string().as_bytes()).await;
        let _ = socket.write_all(b"\n").await;

        return Err(io::Error::new(io::ErrorKind::InvalidData, error_msg));
    }

    buf.truncate(n);

    match String::from_utf8(buf) {
        Ok(data) => {
            match serde_json::from_str::<Value>(&data) {
                Ok(json) => {
                    Ok(Some(json))
                },
                Err(e) => {
                    let error_msg = format!("Invalid JSON format: {}", e);
                    error!("{}", error_msg);

                    let error_response = json!({
                        "status": "error",
                        "message": error_msg
                    });

                    let _ = socket.write_all(error_response.to_string().as_bytes()).await;
                    let _ = socket.write_all(b"\n").await;

                    Err(io::Error::new(io::ErrorKind::InvalidData, e))
                }
            }
        },
        Err(e) => {
            let error_msg = format!("Invalid UTF-8 data received: {}", e);
            error!("{}", error_msg);

            let error_response = json!({
                "status": "error",
                "message": error_msg
            });

            let _ = socket.write_all(error_response.to_string().as_bytes()).await;
            let _ = socket.write_all(b"\n").await;

            Err(io::Error::new(io::ErrorKind::InvalidData, e))
        }
    }
}