use crate::db_operations::admin::reset_database;
use crate::db_operations::bigfiles::process_large_json_file;
use log::{error, info};
use std::process::exit;
use std::sync::Arc;
use crate::db;

pub async fn router(command: &str, db_handler: Arc<db::DatabaseCluster>) -> Result<bool, String> {
    match command {
        "exit" => {
            info!("Exiting application...");
            exit(0);
        }
        "reset" => {
            info!("Resetting the server...");
            let db = db_handler.get_system_db().await;
            match reset_database(&db).await {
                Ok(_) => {
                    info!("Database reset successfully");
                    Ok(true)
                },
                Err(e) => {
                    error!("Failed to reset database: {}", e);
                    Err(format!("Failed to reset database: {}", e))
                }
            }
        }
        "load" => {
            info!{"Load Json from Server..."};
            let db = db_handler.get_main_db().await;
            match process_large_json_file(&db).await{
                Ok(_) => {
                    info!("Successfull add");
                    Ok(true)
                },
                Err(e) => {
                    error!("Failed to load big json file: {}", e);
                    Err(format!("Failed to load big json file: {}", e))
                }
            }}

        "help" => {
            info!("Available commands: exit, init, help, status");
            Ok(true)
        }
        "status" => {
            Ok(true)
        }
        _ => {
            error!("Invalid command: {}", command);
            Err(format!("Invalid command: {}", command))
        },
    }
}