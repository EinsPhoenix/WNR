#![allow(dead_code, unused_imports)]
use log::{info, error};
use neo4rs::{Graph, Error as Neo4jError, ConfigBuilder};
use std::env;
use std::sync::Arc;
use tokio::sync::OnceCell;

pub struct DatabaseCluster {
    main_node: Arc<Graph>,
    system_nodes: Vec<Arc<Graph>>,
}

impl DatabaseCluster {
    pub async fn new() -> Result<Self, DbError> {
        info!("Initializing DatabaseCluster...");
        dotenv::dotenv().ok();

        let uri_main = env::var("NEO4J_URI_WRITE_1").map_err(|e| {
            error!("Failed to read NEO4J_URI_WRITE_1: {}", e);
            DbError::ConnectionError(e.to_string())
        })?;
        let uri_server_admin = env::var("NEO4j_URI_ADMIN").map_err(|e| {
            error!("Failed to read NEO4j_URI_ADMIN: {}", e);
            DbError::ConnectionError(e.to_string())
        })?;

        let main_node = Arc::new(Self::connect_db(&uri_main, 1).await?);
        let system_nodes = vec![Arc::new(Self::connect_db(&uri_server_admin, 0).await?)];

        info!("DatabaseCluster successfully initialized.");
        Ok(Self {
            main_node,
            system_nodes,
        })
    }

    async fn connect_db(uri: &str, usecase: i32) -> Result<Graph, DbError> {
        info!("Connecting to Neo4j at {} with usecase {}", uri, usecase);
        let username = env::var("DATABASE_USER").map_err(|e| {
            error!("DATABASE_USER env variable is missing: {}", e);
            DbError::ConnectionError("Missing DATABASE_USER".into())
        })?;
        let password = env::var("DATABASE_PASSWORD").map_err(|e| {
            error!("DATABASE_PASSWORD env variable is missing: {}", e);
            DbError::ConnectionError("Missing DATABASE_PASSWORD".into())
        })?;
        let default_database = env::var("DEFAULT_DATABASE").map_err(|e| {
            error!("DEFAULT_DATABASE env variable is missing: {}", e);
            DbError::ConnectionError("Missing DEFAULT_DATABASE".into())
        })?;

        let graph_result = match usecase {
            0 => {
                let config = ConfigBuilder::default()
                    .uri(uri)
                    .user(&username)
                    .password(&password)
                    .db("system")
                    .build()
                    .map_err(|e| {
                        error!("Failed to build config for system db: {:?}", e);
                        DbError::ConnectionError(format!("Failed to build config for system db: {:?}", e))
                    })?;
                Graph::connect(config).await
            },
            1 => {
                 let config = ConfigBuilder::default()
                    .uri(uri)
                    .user(&username)
                    .password(&password)
                    .db(default_database.as_str())
                    .build()
                    .map_err(|e| {
                        error!("Failed to build config for standard db: {:?}", e);
                        DbError::ConnectionError(format!("Failed to build config for standard db: {:?}", e))
                    })?;
                Graph::connect(config).await
            }
            _ => {
                error!("Invalid usecase provided for connect_db: {}", usecase);
                return Err(DbError::ConnectionError(format!("Invalid usecase: {}", usecase)));
            }
        };

        graph_result.map_err(|e| {
            error!("Connection to Neo4j failed for usecase {} at {}: {:?}", usecase, uri, e);
            DbError::Neo4jError(e)
        }).map(|graph| {
             info!("Successfully connected to Neo4j for usecase {} at {}", usecase, uri);
             graph
        })
    }

    pub async fn get_main_db(&self) -> Arc<Graph> {
        Arc::clone(&self.main_node)
    }

    pub async fn get_system_db(&self) -> Arc<Graph> {
        Arc::clone(&self.system_nodes[0])
    }
}

pub static DB: OnceCell<Arc<DatabaseCluster>> = OnceCell::const_new();

pub async fn get_database() -> Result<Arc<DatabaseCluster>, DbError> {
    DB.get_or_try_init(|| async {
        let db = DatabaseCluster::new().await?;
        Ok(Arc::new(db))
    })
    .await
    .map(Arc::clone)
}



#[derive(Debug)]
pub enum DbError {
    Neo4jError(Neo4jError),
    ConnectionError(String),
    OtherError(String),
}

impl From<Neo4jError> for DbError {
    fn from(error: Neo4jError) -> Self {
        DbError::Neo4jError(error)
    }
}

impl From<String> for DbError {
    fn from(error: String) -> Self {
        DbError::ConnectionError(error)
    }
}