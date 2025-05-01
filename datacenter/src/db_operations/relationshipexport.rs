use neo4rs::{Graph, query};
use log::{error, info};
use serde_json::Value;

// Exports all relationships from multiple database shards as JSON, with an optional limit on the number of paths.
// Input: &Graph - a reference to the Neo4j graph instance, limit - optional maximum number of paths to retrieve.
// Returns: Option<Value> - JSON array of paths or None if no paths are found.
pub async fn export_all_with_relationships(graph: &Graph, limit: Option<usize>) -> Option<Value> {
   
    let mut path_count = 0;
    let max_paths = limit.unwrap_or(usize::MAX);
    
    let mut all_paths = Vec::new();
    
    // Retrieves relationships from a specific database shard as JSON, with an optional limit on the number of paths.
    // Input: &Graph - a reference to the Neo4j graph instance, shard_name - the name of the shard, remaining_limit - optional limit for paths.
    // Returns: Result<Value, String> - JSON array of paths or an error message.
    async fn get_shard_paths(graph: &Graph, shard_name: &str, remaining_limit: Option<usize>) -> Result<Value, String> {
      
        let limit_clause = match remaining_limit {
            Some(l) => format!("LIMIT {}", l),
            None => "".to_string()
        };
        
        let query_str = format!(r#"
            USE fabric.{}
            MATCH p=()-[]->() 
            WITH p
            {}  
            WITH collect(p) AS paths
            RETURN apoc.convert.toJson(paths) AS json_result
        "#, shard_name, limit_clause);
        
        let query = query(&query_str);
        
        match graph.execute(query).await {
            Ok(mut result) => {
                if let Ok(Some(row)) = result.next().await {
                    if let Ok(json_str) = row.get::<String>("json_result") {
                        match serde_json::from_str(&json_str) {
                            Ok(value) => Ok(value),
                            Err(e) => Err(format!("Failed to parse JSON from {}: {}", shard_name, e))
                        }
                    } else {
                        Err(format!("Failed to get JSON result from row in {}", shard_name))
                    }
                } else {
                    Ok(serde_json::Value::Array(Vec::new()))
                }
            },
            Err(e) => {
                Err(format!("Failed to execute Neo4j query for {}: {}", shard_name, e))
            }
        }
    }
    
    match get_shard_paths(graph, "dbshard1", limit).await {
        Ok(shard1_value) => {
            if let Some(paths) = shard1_value.as_array() {
                path_count += paths.len();
                all_paths.extend(paths.clone());
                info!("Retrieved {} paths from shard1", paths.len());
            }
        },
        Err(e) => {
            error!("Error retrieving paths from shard1: {}", e);
        }
    }
    
    if path_count < max_paths {
        let remaining = if max_paths == usize::MAX { None } else { Some(max_paths - path_count) };
        match get_shard_paths(graph, "dbshard2", remaining).await {
            Ok(shard2_value) => {
                if let Some(paths) = shard2_value.as_array() {
                    path_count += paths.len();
                    all_paths.extend(paths.clone());
                    info!("Retrieved {} paths from shard2", paths.len());
                }
            },
            Err(e) => {
                error!("Error retrieving paths from shard2: {}", e);
            }
        }
    }
    
    if path_count < max_paths {
        let remaining = if max_paths == usize::MAX { None } else { Some(max_paths - path_count) };
        match get_shard_paths(graph, "dbshard3", remaining).await {
            Ok(shard3_value) => {
                if let Some(paths) = shard3_value.as_array() {
                    path_count += paths.len();
                    all_paths.extend(paths.clone());
                    info!("Retrieved {} paths from shard3", paths.len());
                }
            },
            Err(e) => {
                error!("Error retrieving paths from shard3: {}", e);
            }
        }
    }

    if all_paths.is_empty() {
        info!("No paths were found across all shards");
    } else {
        info!("Retrieved a total of {} paths across all shards", all_paths.len());
    }
    
    Some(Value::Array(all_paths))
}