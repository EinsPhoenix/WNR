use log::{info, error};
use serde_json::json; 
use std::sync::Arc;
use tokio::net::{TcpListener, TcpStream};
use tokio_tungstenite::accept_async;
use tokio_tungstenite::tungstenite::Message; 
use futures_util::{SinkExt, StreamExt};
use std::collections::HashMap;
use tokio::sync::{RwLock, broadcast};

pub struct WebRtcServer {
    clients: Arc<RwLock<HashMap<String, broadcast::Sender<String>>>>,
    port: u16,
}

impl WebRtcServer {
    pub fn new(port: u16) -> Self {
        Self {
            clients: Arc::new(RwLock::new(HashMap::new())),
            port,
        }
    }

    pub async fn start(&self) -> Result<(), Box<dyn std::error::Error>> {
        let listener = TcpListener::bind(format!("0.0.0.0:{}", self.port)).await?;
        info!("WebRTC server listening on port {}", self.port);

        while let Ok((stream, addr)) = listener.accept().await {
            info!("New connection from: {}", addr);
            let clients = Arc::clone(&self.clients);
            tokio::spawn(async move {
                if let Err(e) = handle_connection(stream, clients, addr.to_string()).await {
                    error!("Error handling connection {}: {}", addr, e);
                }
            });
        }

        Ok(())
    }

    pub async fn broadcast_video_frame(&self, frame_data: &str, frame_index: usize) -> Result<(), String> {
        let message = json!({
            "type": "video_frame",
            "frame_index": frame_index,
            "frame_data": frame_data,
            "timestamp": chrono::Utc::now().to_rfc3339()
        }).to_string();

        let clients = self.clients.read().await;
        let mut disconnected_clients = Vec::new();

        for (client_id, sender) in clients.iter() {
            if let Err(_) = sender.send(message.clone()) {
                disconnected_clients.push(client_id.clone());
            }
        }

      
        drop(clients);
        if !disconnected_clients.is_empty() {
            let mut clients = self.clients.write().await;
            for client_id in disconnected_clients {
                clients.remove(&client_id);
                info!("Removed disconnected client: {}", client_id);
            }
        }

        Ok(())
    }

    pub async fn broadcast_video_chunks(&self, frame_data: &str, frame_index: usize) -> Result<(), String> {
        const MAX_CHUNK_SIZE: usize = 32000; 
        
        let frame_bytes = frame_data.len();
        let total_chunks = (frame_bytes + MAX_CHUNK_SIZE - 1) / MAX_CHUNK_SIZE;
        
        if total_chunks == 1 {
            
            self.broadcast_video_frame(frame_data, frame_index).await?;
        } else {
            
            let frame_info = json!({
                "type": "video_frame_start",
                "frame_index": frame_index,
                "total_chunks": total_chunks,
                "total_size": frame_bytes,
                "timestamp": chrono::Utc::now().to_rfc3339()
            }).to_string();

            self.broadcast_message(&frame_info).await?;

            
            for chunk_index in 0..total_chunks {
                let start = chunk_index * MAX_CHUNK_SIZE;
                let end = std::cmp::min(start + MAX_CHUNK_SIZE, frame_bytes);
                let chunk_data = &frame_data[start..end];

                let chunk_message = json!({
                    "type": "video_frame_chunk",
                    "frame_index": frame_index,
                    "chunk_index": chunk_index,
                    "total_chunks": total_chunks,
                    "chunk_data": chunk_data,
                    "is_last_chunk": chunk_index == total_chunks - 1,
                    "timestamp": chrono::Utc::now().to_rfc3339()
                }).to_string();

                self.broadcast_message(&chunk_message).await?;
                
            }
        }

        Ok(())
    }

    async fn broadcast_message(&self, message: &String) -> Result<(), String> { 
        let clients = self.clients.read().await;
        let mut disconnected_clients = Vec::new();

        for (client_id, sender) in clients.iter() {
            if let Err(_) = sender.send(message.clone()) { 
                disconnected_clients.push(client_id.clone());
            }
        }

        
        drop(clients);
        if !disconnected_clients.is_empty() {
            let mut clients = self.clients.write().await;
            for client_id in disconnected_clients {
                clients.remove(&client_id);
                info!("Removed disconnected client: {}", client_id);
            }
        }

        Ok(())
    }

    pub async fn get_client_count(&self) -> usize {
        self.clients.read().await.len()
    }
}

async fn handle_connection(
    raw_stream: TcpStream,
    clients: Arc<RwLock<HashMap<String, broadcast::Sender<String>>>>,
    client_id: String,
) -> Result<(), Box<dyn std::error::Error>> {
    let ws_stream = accept_async(raw_stream).await?;
    info!("WebSocket connection established with {}", client_id);

    let (mut ws_sender, mut ws_receiver) = ws_stream.split();
    let (tx, mut rx) = broadcast::channel::<String>(1000);

    
    {
        let mut clients_guard = clients.write().await;
        clients_guard.insert(client_id.clone(), tx);
    }

    
    let client_id_clone = client_id.clone();
    let outgoing_task = tokio::spawn(async move {
        while let Ok(message) = rx.recv().await {
            if let Err(e) = ws_sender.send(Message::Text(message.into())).await {
                error!("Error sending message to client {}: {}", client_id_clone, e);
                break;
            }
        }
    });

    
    while let Some(msg) = ws_receiver.next().await {
        match msg {
            Ok(Message::Text(text)) => {
                info!("Received message from {}: {}", client_id, text);
                
            }
            Ok(Message::Close(_)) => {
                info!("Client {} disconnected", client_id);
                break;
            }
            Err(e) => {
                error!("WebSocket error for client {}: {}", client_id, e);
                break;
            }
            _ => {}
        }
    }

    
    outgoing_task.abort();
    {
        let mut clients_guard = clients.write().await;
        clients_guard.remove(&client_id);
    }
    info!("Client {} cleaned up", client_id);

    Ok(())
}