use neo4rs::{Graph, query, BoltList, BoltType};
use log::{error, info};
use rand::{Rng, SeedableRng, rngs::StdRng};  
use rand::prelude::*;
use chrono::{NaiveDate, NaiveTime};
use std::time::Instant;

use crate::db_operations::sharding::get_current_max_id;

// Resets the database by deleting all nodes.
// Input: &Graph - a reference to the Neo4j graph instance.
// Returns: Result<bool, String> - true if successful, error message otherwise.
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

// Removes the test database by stopping and dropping it.
// Input: &Graph - a reference to the Neo4j graph instance.
// Returns: Result<bool, String> - true if successful, error message otherwise.
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

// Generates a large amount of data and inserts it into multiple database shards efficiently.
// Input: &Graph - a reference to the Neo4j graph instance, count - number of records to generate.
// Returns: Result<usize, String> - the number of successfully inserted records or an error message.
pub async fn generate_data_fast(graph: &Graph, count: usize) -> Result<usize, String> {
    let start_time = Instant::now();
    info!("Starting fast data generation of {} records", count);

    let highest_id = match get_current_max_id(graph, count as i64).await {
        Ok(id) => id,
        Err(e) => return Err(format!("Failed to get highest ID: {}", e))
    };
    
    info!("Current highest ID: {}, will generate IDs from {} to {}", 
          highest_id, highest_id + 1, highest_id + count as i64);

    const BATCH_SIZE: usize = 1000;
    let colors = ["red", "blue", "green", "yellow", "purple", "orange", "black", "white", "gray", "brown"];
    let base_date = NaiveDate::from_ymd_opt(2024, 1, 1).unwrap();
    let mut processed_count = 0;

    for batch_start in (0..count).step_by(BATCH_SIZE) {
        let batch_size = std::cmp::min(BATCH_SIZE, count - batch_start);
        let batch_start_time = Instant::now();
        
        let mut rng = StdRng::from_seed(rand::rng().random());
        
        let mut batch_data = Vec::with_capacity(batch_size);
        for i in 0..batch_size {
            let current_id = highest_id + 1 + (batch_start + i) as i64;
            let random_uuid = format!("auto-gen-{}", current_id);
            let random_color = colors.choose(&mut rng).unwrap();
            let temperature = (rng.random_range(150..350) as f64) / 10.0;
            let humidity = rng.random_range(30..90) as f64;
            
            let random_days = rng.random_range(0..365);
            let random_hours = rng.random_range(0..24);
            let random_minutes = rng.random_range(0..60);
            let date_time = base_date
                .and_time(NaiveTime::from_hms_opt(random_hours, random_minutes, 0).unwrap())
                + chrono::Duration::days(random_days);
            let timestamp = date_time.format("%Y-%m-%d %H:%M:%S").to_string();
            
            let energy_consume = (rng.random_range(10..100) as f64) / 100.0;
            let energy_cost = (rng.random_range(5..50) as f64) / 1000.0;
            batch_data.push((current_id, random_uuid, random_color.to_string(),
                            temperature, humidity, timestamp, energy_consume, energy_cost));
        } 

        let shard1_query = r#"
       USE fabric.dbshard1
    UNWIND $batch AS row
    CREATE (id_node:Id {value: row[0]})
    CREATE (uuid_node:Uuid {value: row[1]})
    MERGE (color_node:Color {value: row[2]})
    MERGE (id_node)-[:HAS_UUID]->(uuid_node)
    MERGE (id_node)-[:HAS_COLOR]->(color_node)
    RETURN id_node.value AS nodeId
        "#;
        
        let batch_params = batch_data.iter()
            .map(|(id, uuid, color, _, _, _, _, _)| {
                let row_list: BoltList = vec![
                    (*id).into(),
                    uuid.clone().into(),
                    color.clone().into(),
                ].into();
                BoltType::List(row_list) 
            })
            .collect::<Vec<BoltType>>(); 

            let params = query(shard1_query).param("batch", batch_params);
            match graph.execute(params).await {
                Ok(mut result) => {
                    info!("Shard 1 batch completed successfully");
                    
                    while let Ok(Some(row)) = result.next().await {
                        if let Ok(id) = row.get::<i64>("nodeId") {
                            println!("Created shard1 node with ID: {}", id);
                        }
                    }
                },
                Err(e) => {
                    error!("Shard 1 batch failed: {}", e);
                    return Err(format!("Shard 1 batch failed: {}", e));
                }
            }
        
        let shard2_query = r#"
            USE fabric.dbshard2
            UNWIND $batch AS row
            MERGE (id_node:Id {value: row[0]})
            CREATE (sensor_data_node:SensorData {timestamp: datetime()})
            MERGE (temp_node:Temperature {value: row[1]})
            MERGE (hum_node:Humidity {value: row[2]})
            MERGE (id_node)-[:HAS_SENSOR_DATA]->(sensor_data_node)
            MERGE (sensor_data_node)-[:MEASURES_TEMPERATURE]->(temp_node)
            MERGE (sensor_data_node)-[:MEASURES_HUMIDITY]->(hum_node)
            RETURN id_node.value AS nodeId
        "#;
       
        let batch_params = batch_data.iter()
            .map(|(id, _, _, temp, hum, _, _, _)| {
                let row_list: BoltList = vec![
                    (*id).into(),
                    (*temp).into(),
                    (*hum).into(),
                ].into();
                BoltType::List(row_list)
            })
            .collect::<Vec<BoltType>>();

            let params = query(shard2_query).param("batch", batch_params);
            match graph.execute(params).await {
                Ok(mut result) => {
                    info!("Shard 2 batch completed successfully");
                    
                    while let Ok(Some(row)) = result.next().await {
                        if let Ok(id) = row.get::<i64>("nodeId") {
                            println!("Created shard2 node with ID: {}", id);
                        }
                    }
                },
                Err(e) => {
                    error!("Shard 2 batch failed: {}", e);
                    return Err(format!("Shard 2 batch failed: {}", e));
                }
            }
        
        let shard3_query = r#"
        USE fabric.dbshard3
        UNWIND $batch AS row
        MERGE (id:Id {value: row[0]})
        MERGE (ts:Timestamp {value: row[1]})
        CREATE (econsume:EnergyConsumption {value: row[2]})
        CREATE (ecost:EnergyCost {value: row[3]})
        MERGE (id)-[:HAS_TIMESTAMP]->(ts)
        MERGE (id)-[:HAS_ENERGY_CONSUMPTION]->(econsume)
        MERGE (econsume)-[:HAS_ENERGY_COST]->(ecost)
        RETURN id.value AS nodeId
        "#;
        
        let batch_params = batch_data.iter()
            .map(|(id, _, _, _, _, timestamp, energy_consume, energy_cost)| {
                let row_list: BoltList = vec![
                    (*id).into(),
                    timestamp.clone().into(),
                    (*energy_consume).into(),
                    (*energy_cost).into(),
                ].into();
                BoltType::List(row_list)
            })
            .collect::<Vec<BoltType>>();
        let shard3_params = query(shard3_query).param("batch", batch_params);
        match graph.execute(shard3_params).await {
            Ok(mut result) => {
                info!("Shard 3 batch completed successfully");
                
                while let Ok(Some(row)) = result.next().await {
                    if let Ok(id) = row.get::<i64>("nodeId") {
                        println!("Created node with ID: {}", id);
                    }
                }
            },
            Err(e) => {
                error!("Shard 3 batch failed: {}", e);
                return Err(format!("Shard 3 batch failed: {}", e));
            }
        }
        
        processed_count += batch_size;
        let batch_time = batch_start_time.elapsed();
        info!("Batch completed: {}/{} records, batch time: {:.2?}, speed: {:.2} records/sec", 
              processed_count, count, batch_time, batch_size as f64 / batch_time.as_secs_f64());
        }
    
    let total_time = start_time.elapsed();
    info!("Fast data generation completed: inserted {} records in {:.2?}", 
          processed_count, total_time);
    info!("Average speed: {:.2} records/second", 
          processed_count as f64 / total_time.as_secs_f64());
    
    Ok(processed_count)
}
