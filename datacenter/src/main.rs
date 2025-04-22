use log::{info, error};
use dotenv::dotenv;
use std::env;
use tokio::net::{TcpListener, TcpStream};
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use std::io;
use serde_json::{json, Value};
use std::sync::Arc;
use fern::Dispatch;
use chrono::Local;

mod db;
mod auth;
mod ip_payload_handler;
mod mqtt_handler;
mod command_handler;

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
    
    if env_logger::try_init().is_err() {
        eprintln!("Logger already initialized.");
    }
    info!("Starting the server...");

    let db_handler = db::get_database().await.unwrap();
    
   
    let db_mqtt_handler_clone = Arc::clone(&db_handler);

    tokio::spawn(async move {
        if let Err(e) = mqtt_handler::start_mqtt_client(db_mqtt_handler_clone).await {
            error!("MQTT client error: {:?}", e);
        }
    });

    let password = env::var("SERVER_PASSWORD").expect("SERVER_PASSWORD not set in .env");
    let listener = TcpListener::bind("0.0.0.0:12345").await?;
    info!("Server is listening on 0.0.0.0:12345");
    
    loop {
        match listener.accept().await {
            Ok((socket, addr)) => {
                info!("New connection from: {}", addr);
                let password_clone = password.clone();
               
                let db_handler_clone = Arc::clone(&db_handler);
                tokio::spawn(async move {
                    if let Err(e) = handle_client(socket, password_clone, db_handler_clone).await {
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
    db_handler: Arc<db::DatabaseCluster> 
) -> io::Result<()> {
    if !auth::authenticate_client(&mut socket, &correct_password).await? {
        return Ok(());
    }
    
    loop {
        match receive_json(&mut socket).await {
            Ok(Some(json)) => {
                if let Err(e) = ip_payload_handler::process_json(&json, Arc::clone(&db_handler), &mut socket).await {
                    error!("Error processing JSON: {}", e);
                    
                }
            },
            Ok(None) => {
                info!("Client disconnected.");
                break;
            },
            Err(e) => {
                error!("Error receiving JSON: {:?}", e);
                
                break;
            }
        }
    }
    
    Ok(())
}

async fn receive_json(socket: &mut TcpStream) -> io::Result<Option<Value>> {
    // maximum JSON size 10MB
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
            info!("Received data size: {} bytes", data.len());
            match serde_json::from_str::<Value>(&data) {
                Ok(json) => {
                    info!("JSON successfully parsed");
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