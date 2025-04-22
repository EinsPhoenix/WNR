use log::info;
use std::io;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpStream;

pub async fn authenticate_client(socket: &mut TcpStream, correct_password: &str) -> io::Result<bool> {
    let mut buffer = [0; 1024];
    
    socket.write_all(b"Enter password: ").await?;
    let n = socket.read(&mut buffer).await?;
    
    if n == 0 {
        info!("Client disconnected during authentication.");
        return Ok(false);
    }
    
    let received_password = String::from_utf8_lossy(&buffer[..n]).trim().to_string();
    
    if received_password == correct_password {
        socket.write_all(b"Access granted. You can now send JSON messages.\n").await?;
        info!("Client authenticated successfully.");
        Ok(true)
    } else {
        socket.write_all(b"Access denied.\n").await?;
        info!("Client provided wrong password.");
        socket.shutdown().await?;
        Ok(false)
    }
}