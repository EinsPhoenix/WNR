use log::{info, error};
use neo4rs::{Graph, Error as Neo4jError, ConfigBuilder};
use std::env;
use std::sync::Arc;
use tokio::sync::OnceCell;

pub struct DatabaseCluster {
    primary_nodes: Vec<Arc<Graph>>,
    secondary_nodes: Vec<Arc<Graph>>,
    system_nodes: Vec<Arc<Graph>>,
}

impl DatabaseCluster {
    pub async fn new() -> Result<Self, DbError> {
        info!("Initializing DatabaseCluster...");
        dotenv::dotenv().ok();

        let uri_server1 = env::var("NEO4J_URI_WRITE_1").map_err(|e| {
            error!("Failed to read NEO4J_URI_WRITE_1: {}", e);
            DbError::ConnectionError(e.to_string())
        })?;
        let uri_server2 = env::var("NEO4J_URI_WRITE_2").map_err(|e| {
            error!("Failed to read NEO4J_URI_WRITE_2: {}", e);
            DbError::ConnectionError(e.to_string())
        })?;
        let uri_server3 = env::var("NEO4J_URI_READ_3").map_err(|e| {
            error!("Failed to read NEO4J_URI_READ_3: {}", e);
            DbError::ConnectionError(e.to_string())
        })?;
        let uri_server_admin = env::var("NEO4j_URI_ADMIN").map_err(|e| {
            error!("Failed to NEO4j_URI_ADMIN: {}", e);
            DbError::ConnectionError(e.to_string())
        })?;

        let primary_nodes = vec![Arc::new(Self::connect_db(&uri_server1, false).await?)];
        let secondary_nodes = vec![
            Arc::new(Self::connect_db(&uri_server3, false).await?),
            Arc::new(Self::connect_db(&uri_server2, false).await?),
        ];

        let system_nodes = vec![Arc::new(Self::connect_db(&uri_server_admin, true).await?)];

        info!("DatabaseCluster successfully initialized.");
        Ok(Self {
            primary_nodes,
            secondary_nodes,
            system_nodes
        })
    }

    async fn connect_db(uri: &str, use_system: bool) -> Result<Graph, DbError> {
        info!("Connecting to Neo4j at {}", uri);
        let username = env::var("DATABASE_USER").map_err(|e| {
            error!("DATABASE_USER env variable is missing: {}", e);
            DbError::ConnectionError("Missing DATABASE_USER".into())
        })?;
        let password = env::var("DATABASE_PASSWORD").map_err(|e| {
            error!("DATABASE_PASSWORD env variable is missing: {}", e);
            DbError::ConnectionError("Missing DATABASE_PASSWORD".into())
        })?;

        let graph = if use_system {
            let config = ConfigBuilder::default()
                .uri(uri)
                .user(&username)
                .password(&password)
                .db("system")
                .build()
                .map_err(|e| {
                    error!("Failed to build config: {:?}", e);
                    DbError::ConnectionError(format!("Failed to build config: {:?}", e))
                })?;

            Graph::connect(config)
                .await
                .map_err(|e| {
                    error!("Connection to Neo4j system database failed at {}: {:?}", uri, e);
                    DbError::Neo4jError(e)
                })?
        } else {
            Graph::new(uri, &username, &password)
                .await
                .map_err(|e| {
                    error!("Connection to Neo4j failed at {}: {:?}", uri, e);
                    DbError::Neo4jError(e)
                })?
        };

        info!("Successfully connected to Neo4j at {}", uri);
        Ok(graph)
    }

    pub async fn get_primary_db(&self) -> Arc<Graph> {
        Arc::clone(&self.primary_nodes[0])
    }

    pub async fn get_read_db(&self, number: usize) -> Arc<Graph> {
        let index = number % self.secondary_nodes.len();
        Arc::clone(&self.secondary_nodes[index])
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