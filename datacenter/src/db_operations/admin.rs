use neo4rs::{Graph, query};
use log::{error};





pub async fn alter_database(graph: &Graph) -> Result<bool, String> {
    
    let delete_query = query(r#"
       
        ALTER DATABASE neo4j SET TOPOLOGY 1 PRIMARIES 2 SECONDARIES;
      
    "#);

    match graph.execute(delete_query).await {
        Ok(_) => {
            log::info!("Database successfully altered");
            Ok(true)
        },
        Err(e) => {
            let error_msg = format!("There was an issue altering the database {}", e);
            error!("{}", error_msg);
            return Err(error_msg);
        }
    }

}

pub async fn index_database(graph: &Graph) -> Result<bool, String> {
   
    let index_statements = [
        "CREATE INDEX FOR (u:UUID) ON (u.id)",
        "CREATE INDEX FOR (c:Color) ON (c.value)",
        "CREATE INDEX FOR (t:Temperature) ON (t.value)",
        "CREATE INDEX FOR (h:Humidity) ON (h.value)",
        "CREATE INDEX FOR (ts:Timestamp) ON (ts.value)",
        "CREATE INDEX FOR (ec:EnergyCost) ON (ec.value)",
        "CREATE INDEX FOR (e:EnergyConsume) ON (e.value)"
    ];
    
    for statement in index_statements {
        match graph.execute(query(statement)).await {
            Ok(_) => {
                log::info!("Created index: {}", statement);
            },
            Err(e) => {
                let error_msg = format!("Failed to create index '{}': {}", statement, e);
                error!("{}", error_msg);
                return Err(error_msg);
            }
        }
    }
    
    log::info!("Database successfully INDEXED");
    Ok(true)
}

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