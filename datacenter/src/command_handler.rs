use crate::db_operations::admin::*;
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
        "generate" => {
            info!("Generating data...");
            let db = db_handler.get_system_db().await;
            match generate_data_fast(&db, 1000).await {
                Ok(count) => {
                    info!("Generated {} records successfully", count);
                    Ok(true)
                },
                Err(e) => {
                    error!("Failed to generate data: {}", e);
                    Err(format!("Failed to generate data: {}", e))
                }
            }
        }

        "help" => {
            info!("Available commands: exit, help, status, generate");
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