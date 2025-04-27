use log::{info, error};
use neo4rs::{Graph, Error as Neo4jError, ConfigBuilder, query};
use std::env;
use std::sync::Arc;
use tokio::sync::OnceCell;
use crate::db_operations::admin::remove_test_database;

pub struct DatabaseCluster {
    main_node: Arc<Graph>,
    system_nodes: Vec<Arc<Graph>>,
    test_db: Option<Arc<Graph>>,
}

impl DatabaseCluster {
    pub async fn new() -> Result<Self, DbError> {
        info!("Initializing DatabaseCluster...");
        dotenv::dotenv().ok();

        let is_test = env::var("TEST").map_err(|e| {
            error!("Failed to read TEST environment variable: {}", e);
            DbError::ConnectionError(format!("Failed to read TEST environment variable: {}", e))
        })?;

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

        let mut test_db = None;

        if is_test.to_string() == "true" {
            info!("TEST environment variable is set. Initializing test database...");

            let system_db_conn = Arc::clone(&system_nodes[0]);

            info!("Ensuring 'Test' database exists...");
            let create_db_query = query("CREATE DATABASE Test IF NOT EXISTS");
            match system_db_conn.run(create_db_query).await {
                Ok(_) => info!("'Test' database ensured successfully or already exists."),
                Err(e) => {
                    error!("Failed to execute 'CREATE DATABASE Test': {:?}", e);
                    error!("Continuing without dedicated test database connection due to creation error.");
                }
            }

            tokio::time::sleep(tokio::time::Duration::from_secs(1)).await;

            info!("Connecting to 'Test' database...");
            match Self::connect_db(&uri_server_admin, 2).await {
                Ok(conn) => {
                    test_db = Some(Arc::new(conn));
                    info!("Successfully connected to 'Test' database.");
                }
                Err(e) => {
                    error!("Failed to connect to 'Test' database: {:?}. Test database connection will be unavailable.", e);
                }
            }
        } else {
            info!("TEST environment variable not set. Skipping test database initialization.");
            let system_db_conn = Arc::clone(&system_nodes[0]);

            info!("Checking if 'Test' database exists before potential removal...");
            let check_db_query = query("SHOW DATABASES WHERE name = 'Test' YIELD name");
            match system_db_conn.execute(check_db_query).await {
                Ok(mut stream) => {
                    match stream.next().await {
                        Ok(Some(_row)) => {
                            info!("'Test' database found. Attempting removal...");
                            match remove_test_database(&system_db_conn).await {
                                Ok(_) => info!("'Test' database removed successfully."),
                                Err(e) => {
                                    error!("Failed to remove 'Test' database: {:?}", e);
                                }
                            }
                        }
                        Ok(None) => {
                            info!("'Test' database does not exist. No removal needed.");
                        }
                        Err(e) => {
                            error!("Error while checking 'Test' database existence stream: {:?}", e);
                        }
                    }
                }
                Err(e) => {
                    error!("Failed to execute query to check for 'Test' database existence: {:?}", e);
                }
            }
        }

        info!("DatabaseCluster successfully initialized.");
        Ok(Self {
            main_node,
            system_nodes,
            test_db,
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
            2 => {
                let config = ConfigBuilder::default()
                    .uri(uri)
                    .user(&username)
                    .password(&password)
                    .db("Test")
                    .build()
                    .map_err(|e| {
                        error!("Failed to build config for test db: {:?}", e);
                        DbError::ConnectionError(format!("Failed to build config for test db: {:?}", e))
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

    pub async fn get_test_db(&self) -> Result<Arc<Graph>, DbError> {
        match &self.test_db {
            Some(db) => Ok(Arc::clone(db)),
            None => Err(DbError::ConnectionError("Test database is not initialized or connection failed.".to_string())),
        }
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