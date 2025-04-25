use neo4rs::{Graph, query};
use log::{error};

pub async fn reset_database(graph: &Graph) -> Result<bool, String> {
    
    let delete_query = query(r#"
        MATCH (n) DETACH DELETE n
    "#);

    match graph.execute(delete_query).await {
        Ok(_) => {
            log::info!("All nodes succesfully deleted");
            Ok(true)
        },
        Err(e) => {
            let error_msg = format!("There was a misstake: {}", e);
            error!("{}", error_msg);
            return Err(error_msg);
        }
    }
}

pub async fn remove_test_database(graph: &Graph) -> Result<bool, String> {
    
    let delete_query = query(r#"
        STOP DATABASE Test
        DROP DATABASE Test.alias
        DROP DATABASE Test
    "#);

    match graph.execute(delete_query).await {
        Ok(_) => {
            log::info!("Test database successfully deleted");
            Ok(true)
        },
        Err(e) => {
            let error_msg = format!("There was a misstake: {}", e);
            error!("{}", error_msg);
            return Err(error_msg);
        }
    }
}