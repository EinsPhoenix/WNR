// BIG JSON
use std::fs::File;
use std::io::BufReader;
use std::path::PathBuf;
use std::error::Error;

use neo4rs::{Graph, query};
use log::{error, info};
use serde_json::{json, Value, Deserializer};


use crate::db_operations::crud::create_new_relation;


pub async fn process_large_json_file(graph: &Graph) -> Result<bool, Box<dyn Error>> {
    
    let possible_paths = [
        PathBuf::from("data.json"),                    
        PathBuf::from("./data.json"),                  
        PathBuf::from("../data.json"),                 
        PathBuf::from("src/data.json"),               
        PathBuf::from("datacenter/src/data.json"),    
        PathBuf::from("backend_neo/datacenter/src/data.json"), 
        
    ];
    
   
    let mut file_path = None;
    for path in &possible_paths {
        if path.exists() {
            info!("Found data.json at: {}", path.display());
            file_path = Some(path);
            break;
        }
    }
    
    
    let file_path = file_path.ok_or_else(|| {
        let error_msg = format!(
            "data.json not found in any of the expected locations. Checked paths: {:?}",
            possible_paths.iter().map(|p| p.display().to_string()).collect::<Vec<_>>()
        );
        error!("{}", &error_msg);
        error_msg
    })?;

    info!("Opening JSON file at: {}", file_path.display());
    let file = File::open(&file_path)?;
    let file_size = file.metadata()?.len();
    info!("File size: {} bytes ({:.2} MB)", file_size, file_size as f64 / 1_048_576.0);
    
    
    let buffer_size = 1024 * 1024; 
    let reader = BufReader::with_capacity(buffer_size, file);

   
    let stream = Deserializer::from_reader(reader).into_iter::<Value>();
    let mut success_count = 0;
    let mut failure_count = 0;
    let mut processed_count = 0;

 
    info!("Starting JSON processing...");
    for item in stream {
        processed_count += 1;
        if processed_count % 100 == 0 {
            info!("Processed {} items so far...", processed_count);
        }
        
        match item {
            Ok(data) => {
                match create_new_relation(&data, graph).await {
                    Ok(true) => {
                        success_count += 1;
                        if success_count % 100 == 0 {
                            info!("Successfully processed {} records", success_count);
                        }
                    },
                    Ok(false) => {
                      
                    },
                    Err(e) => {
                        error!("Error processing JSON batch: {}", e);
                        failure_count += 1;
                    }
                }
            },
            Err(e) => {
                error!("Error parsing JSON item #{}: {}", processed_count, e);
                failure_count += 1;
                
                
                if failure_count > 10 && processed_count < 20 {
                    return Err("Too many JSON parsing errors. Check if the file format is correct.".into());
                }
            }
        }
    }

    info!("Finished processing JSON file. Total items: {}, Successes: {}, Failures: {}", 
          processed_count, success_count, failure_count);

    if failure_count == 0 {
        Ok(true)
    } else {
        Err(format!("Encountered {} failures while processing {} items", failure_count, processed_count).into())
    }
}

