use neo4rs::{Graph, query};
use log::{error, info, warn};
use serde_json::{json, Value, Deserializer};

pub async fn export_all_with_relationships(graph: &Graph, limit: Option<usize>) -> Option<Value> {
    
    let limit_clause = match limit {
        Some(l) => format!("LIMIT {}", l),
        None => "".to_string()
    };
    
    let query_str = format!(r#"
        MATCH p=()-[]->() 
        {}  
        WITH collect(p) AS paths
        RETURN apoc.convert.toJson(paths) AS json_result;
        
    "#, limit_clause);
    
    let query = query(&query_str);
    
    match graph.execute(query).await {
        Ok(mut result) => {
            if let Ok(Some(row)) = result.next().await {
                if let Ok(json_str) = row.get::<String>("json_result") {
                    match serde_json::from_str(&json_str) {
                        Ok(value) => Some(value),
                        Err(e) => {
                            error!("Failed to parse JSON string: {}", e);
                            None
                        }
                    }
                } else {
                    error!("Failed to get JSON result from row");
                    None
                }
            } else {
                
                Some(serde_json::Value::Array(Vec::new()))
            }
        },
        Err(e) => {
            error!("Failed to execute Neo4j query: {}", e);
            None
        }
    }
}