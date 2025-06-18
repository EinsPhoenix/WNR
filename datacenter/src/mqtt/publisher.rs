use rumqttc::{AsyncClient, QoS};
use serde_json::{Value, json};
use log::{info, error};
use std::error::Error;
use uuid::Uuid;


const MAX_MESSAGE_SIZE: usize = 8000;

pub async fn publish_paginated_results(client: &AsyncClient, topic: &str, payload: &Value) -> Result<(), Box<dyn Error>> {
    let payload_str = serde_json::to_string(payload)?;
    let payload_size = payload_str.len();

    if payload_size <= MAX_MESSAGE_SIZE {
        info!("Publishing directly (fits within limit) to {}: {} bytes", topic, payload_size);
        client.publish(topic, QoS::AtLeastOnce, false, payload_str).await?;
        return Ok(());
    }

    info!("Large message detected ({} bytes), using pagination for topic {}", payload_size, topic);

    let request_id = Uuid::new_v4().to_string();

    let array_payload = match payload {
        Value::Array(items) => items.clone(),
        _ => vec![payload.clone()] 
    };

    let metadata_template = json!({
        "type": "paginated",
        "request_id": &request_id,
        "page": 999, 
        "total_pages": 999, 
        "data": []
    });
   
    let metadata_overhead = serde_json::to_string(&metadata_template)?.len() - 2 + 50; 
    let effective_max_size = MAX_MESSAGE_SIZE.saturating_sub(metadata_overhead);

    if effective_max_size == 0 {
        error!("MAX_MESSAGE_SIZE is too small for pagination metadata.");
        return Err("MAX_MESSAGE_SIZE too small for pagination".into());
    }

    let total_items = array_payload.len();
    let mut items_per_page = 1; 
    if total_items > 0 {
        let approx_sum_of_raw_item_json_sizes = payload_size.saturating_sub(2 + (total_items - 1).max(0)); 
        let avg_raw_item_json_size = (approx_sum_of_raw_item_json_sizes as f64 / total_items as f64).max(1.0) as usize;
        let max_index_digits = if total_items == 1 { 
            1 
        } else {
            (total_items - 1).to_string().len() 
        };
        let tuple_serialization_overhead_estimate = 3 + max_index_digits; 
        let avg_item_tuple_size = (avg_raw_item_json_size + tuple_serialization_overhead_estimate).max(1);
        items_per_page = (effective_max_size / avg_item_tuple_size).max(1);
    }
    let initial_total_pages_estimate = (total_items + items_per_page - 1) / items_per_page; 

    info!("Pagination details: Total Items: {}, Items/Page (est. tuple): ~{}, Total Pages (est.): {}", total_items, items_per_page, initial_total_pages_estimate);

    let mut current_page = 1;
    let mut current_chunk = Vec::new();
    let mut current_chunk_size_estimate = 0; 
  

    for item in array_payload.into_iter().enumerate() {
        let item_json = serde_json::to_string(&item)?;
        let item_size = item_json.len();

        if !current_chunk.is_empty() && current_chunk_size_estimate + item_size + 1 > effective_max_size {
           
            let page_payload = json!({
                "type": "paginated",
                "request_id": &request_id,
                "page": current_page,
                "total_pages": initial_total_pages_estimate, 
                "data": current_chunk
            });

            let page_topic = format!("{}/page/{}", topic, current_page);
            let page_json = serde_json::to_string(&page_payload)?;

            info!("Publishing page {}/{} (estimate) to {} ({} bytes)",
                  current_page, initial_total_pages_estimate, page_topic, page_json.len());

            if page_json.len() > MAX_MESSAGE_SIZE {
                 error!("Calculated page {} size ({}) exceeds MAX_MESSAGE_SIZE ({}). Aborting pagination.", current_page, page_json.len(), MAX_MESSAGE_SIZE);
                 return Err(format!("Page {} too large ({})", current_page, page_json.len()).into());
            }

            client.publish(&page_topic, QoS::AtLeastOnce, false, page_json).await?;

            current_page += 1;
            current_chunk = Vec::new();
            current_chunk_size_estimate = 0;
        } 

        current_chunk.push(item);
        current_chunk_size_estimate += item_size + if current_chunk.len() > 1 { 1 } else { 0 }; 
    }

    let actual_total_pages_count;
    if !current_chunk.is_empty() {
        let page_payload = json!({
            "type": "paginated",
            "request_id": &request_id,
            "page": current_page,
            "total_pages": initial_total_pages_estimate, 
            "data": current_chunk
        });

        let page_topic = format!("{}/page/{}", topic, current_page);
        let page_json = serde_json::to_string(&page_payload)?;

        info!("Publishing final page {}/{} (estimate) to {} ({} bytes)",
              current_page, initial_total_pages_estimate, page_topic, page_json.len());

        if page_json.len() > MAX_MESSAGE_SIZE {
             error!("Calculated final page {} size ({}) exceeds MAX_MESSAGE_SIZE ({}). Aborting pagination.", current_page, page_json.len(), MAX_MESSAGE_SIZE);
             return Err(format!("Final page {} too large ({})", current_page, page_json.len()).into());
        }

        client.publish(&page_topic, QoS::AtLeastOnce, false, page_json).await?;
        actual_total_pages_count = current_page;
    } else {
        if total_items == 0 {
            actual_total_pages_count = 0;
        } else {
            
            
            actual_total_pages_count = current_page - 1;
        }
    }

    
    let summary_payload = json!({
        "type": "summary",
        "request_id": request_id,
        "total_items": total_items,
        "total_pages": actual_total_pages_count, 
        "original_size": payload_size,
        "topic_base": topic
    });

    let summary_topic = format!("{}/summary", topic);
    client.publish(&summary_topic, QoS::AtLeastOnce, false, serde_json::to_string(&summary_payload)?).await?;
    info!("Published summary for request {}: {} total items across {} pages",
          request_id, total_items, actual_total_pages_count);

    Ok(())
}

pub async fn publish_result(client: &AsyncClient, topic: &str, payload: &Value) -> Result<(), Box<dyn Error>> {
    let payload_str = serde_json::to_string(payload)?;
    let payload_size = payload_str.len();

    if payload_size <= MAX_MESSAGE_SIZE {
        info!("Publishing to {}: {} bytes", topic, payload_size);
        client.publish(topic, QoS::AtLeastOnce, false, payload_str).await?;
    } else {
        info!("Message too large for direct publish ({} bytes), using pagination for topic {}", payload_size, topic);
        publish_paginated_results(client, topic, payload).await?;
    }

    Ok(())
}

pub async fn publish_error_response(client: &AsyncClient, client_id: &str, request_type: &str, message: &str) -> Result<(), Box<dyn Error>> {
    let response_topic = format!("rust/response/{}/{}", client_id, request_type);
    let response = json!({
        "status": "error",
        "message": message
    });
    publish_result(client, &response_topic, &response).await
}