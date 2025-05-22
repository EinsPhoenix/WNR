use std::fs::File;
use std::io::{Read, Write, Error as IoError};
use std::path::Path;
use std::time::Duration;
use chrono::Local;
use serde_json::{Value, json};
use rand::Rng; 
use rand::distr::Alphanumeric;

pub async fn log_benchmark(batch_data_len: usize, batch_time: Duration) -> Result<(), IoError> {
    let now = Local::now();
    let random_suffix: String = rand::rng()
        .sample_iter(&Alphanumeric)
        .take(4) 
        .map(char::from)
        .collect();
    let timestamp = format!(
        "batch_{}_{}",
        now.format("%Y_%m_%d_%H_%M_%S_%3f"), 
        random_suffix
    );
    let batch_time_ms = batch_time.as_secs_f64();
    let speed = batch_data_len as f64 / batch_time.as_secs_f64();

    let entry = json!({
        "batchsize": batch_data_len,
        "batchtime": batch_time_ms,
        "speed": speed
    });

    let path = "benchmark.json";
    let mut data: Value = if Path::new(path).exists() {
        let mut file = File::open(path)?;
        let mut content = String::new();
        file.read_to_string(&mut content)?;
        serde_json::from_str(&content).unwrap_or(json!({}))
    } else {
        json!({})
    };

    data[timestamp] = entry;

    let mut file = File::create(path)?;
    file.write_all(serde_json::to_string_pretty(&data).unwrap().as_bytes())?;
    Ok(())
}