# Go back home [🏠](../Database.md)
# 📄 MQTT Request Processor Documentation

This document outlines the functionality of the `request_processor.rs` module, which acts as the central hub for handling incoming MQTT requests within the `datacenter` application. It parses requests, interacts with the Neo4j database cluster (using read replicas and a primary write instance), and publishes results or errors back via MQTT. 🚀

## 📬 General Request Structure

All requests sent to the `datacenter` via MQTT on the `rust/requests` topic **must** adhere to the following JSON structure:

```json
{
  "client_id": "your_unique_client_identifier",
  "request": "the_specific_request_type",
  "data": { ... }
  
}
```

-   `client_id` (String, **Required**): A unique identifier for the client sending the request. This ID is crucial as it's used to route the response back to the correct MQTT topic.
-   `request` (String, **Required**): Specifies the type of operation the client wants to perform. The available request types are detailed below.
-  `data` (Varies): Contains the necessary data for the specific request.

## 📡 API Endpoints (MQTT Request Types)

The processor listens on the `rust/requests` topic. Responses are published to specific topics based on the `client_id` and `request` type. Error responses are generally published to `rust/response/{client_id}/error`.

---

### 1. `uuid` - Fetch Specific Node(s) 🆔

-   **Description:** Retrieves the details of one or more specific nodes based on their UUIDs.
-   **Request Payload:**
    ```json
    {
      "client_id": "frontend_dashboard_1",
      "request": "uuid",
      "payload": [
        { "uuid": "uuid-123-abc" },
        { "uuid": "uuid-456-def" }
      ]
    }
    ```
    -   `payload`: An array of objects, where each object **must** contain a `uuid` (String) key.
-   **Response Topic:** `rust/uuid/{client_id}` (A separate message is published for *each* UUID requested).
-   **Success Response (per UUID):**
    ```json
    // If found
    {
      "uuid": "uuid-123-abc",
      "color": "blue",
      "sensor_data": {
        "temperature": 22.5,
        "humidity": 45.1
      },
      "timestamp": "2025-04-25T10:00:00Z",
      "energy_consume": 1.5,
      "energy_cost": 0.25
    }

    // If not found
    {
      "uuid": "uuid-not-found",
      "found": false,
      "message": "No data found for this UUID"
    }
    ```
-   **Error Response:** Published if the `payload` is missing or not an array.
-   **Notes:** Uses a read replica (`read_conn_1`).

---

### 2. `all` - Fetch All Nodes 🌍

-   **Description:** Retrieves details for *all* UUID nodes stored in the database, ordered by timestamp descending.
-   **Request Payload:**
    ```json
    {
      "client_id": "data_exporter_service",
      "request": "all"
      // No 'payload' or 'data' needed
    }
    ```
-   **Response Topic:** `rust/response/{client_id}/all`
-   **Success Response:**
    ```json
    [
      {
        "uuid": "uuid-789-ghi",
        "color": "green",
        "sensor_data": { "temperature": 21.0, "humidity": 50.0 },
        "timestamp": "2025-04-25T11:00:00Z",
        "energy_consume": 1.2,
        "energy_cost": 0.20
      },
      {
        "uuid": "uuid-123-abc",
        "color": "blue",
        "sensor_data": { "temperature": 22.5, "humidity": 45.1 },
        "timestamp": "2025-04-25T10:00:00Z",
        "energy_consume": 1.5,
        "energy_cost": 0.25
      }
      // ... more nodes
    ]
    ```
    -   Returns an array of node objects (structure same as `uuid` success response).
-   **Error Response:** Published if the database query fails.
-   **Notes:** Uses a read replica (`read_conn_2`). Be cautious, this can return a large amount of data. Consider using `page` for large datasets.

---

### 3. `color` - Filter Nodes by Color 🎨

-   **Description:** Retrieves all UUID nodes that have a specific color.
-   **Request Payload:**
    ```json
    {
      "client_id": "color_analyzer_app",
      "request": "color",
      "data": "red"
    }
    ```
    -   `data`: The color (String) to filter by.
-   **Response Topic:** `rust/response/{client_id}/color`
-   **Success Response:** An array of node objects matching the color (structure same as `uuid` success response).
-   **Error Response:** Published if `data` is missing, not a string, or the query fails.
-   **Notes:** Uses a read replica (`read_conn_2`).

---

### 4. `time_range` - Filter Nodes by Time Range ⏳

-   **Description:** Retrieves all UUID nodes whose timestamp falls within a specified start and end time.
-   **Request Payload:**
    ```json
    {
      "client_id": "history_viewer_01",
      "request": "time_range",
      "start": "2025-04-25T09:00:00Z",
      "end": "2025-04-25T12:00:00Z"
    }
    ```
    -   `start` (String): The start timestamp (inclusive, ISO 8601 format recommended).
    -   `end` (String): The end timestamp (inclusive, ISO 8601 format recommended).
-   **Response Topic:** `rust/response/{client_id}/time_range`
-   **Success Response:** An array of node objects within the time range (structure same as `uuid` success response).
-   **Error Response:** Published if `start` or `end` are missing, not strings, or the query fails.
-   **Notes:** Uses a read replica (`read_conn_1`).

---

### 5. `temperature_humidity` - Filter Nodes by Sensor Values🌡️💧

-   **Description:** Retrieves all UUID nodes matching specific temperature and humidity values.
-   **Request Payload:**
    ```json
    {
      "client_id": "sensor_monitor_widget",
      "request": "temperature_humidity",
      "temperature": 25.0,
      "humidity": 60.5
    }
    ```
    -   `temperature` (Number): The exact temperature value to match.
    -   `humidity` (Number): The exact humidity value to match.
-   **Response Topic:** `rust/response/{client_id}/temperature_humidity`
-   **Success Response:** An array of node objects matching the criteria (structure same as `uuid` success response).
-   **Error Response:** Published if `temperature` or `humidity` are missing, not numbers, or the query fails.
-   **Notes:** Uses a read replica (`read_conn_1`).

---

### 6. `timestamp` - Get Sensor Data at Specific Time ⏱️

-   **Description:** Retrieves the temperature and humidity recorded exactly at a specific timestamp.
-   **Request Payload:**
    ```json
    {
      "client_id": "realtime_graph_component",
      "request": "timestamp",
      "data": "2025-04-25T10:30:15Z"
    }
    ```
    -   `data` (String): The exact timestamp to query (ISO 8601 format recommended).
-   **Response Topic:** `rust/response/{client_id}/timestamp`
-   **Success Response:**
    ```json
    // If data found
    {
      "timestamp": "2025-04-25T10:30:15Z",
      "temperature": 23.1,
      "humidity": 48.9
    }

    // If no data found for that exact timestamp
    {
      "timestamp": "2025-04-25T00:00:00Z",
      "found": false,
      "message": "No temperature/humidity data found for this timestamp"
    }
    ```
-   **Error Response:** Published if `data` is missing, not a string, or the query fails.
-   **Notes:** Uses a read replica (`read_conn_1`). This looks for data linked *directly* to the timestamp node.

---

### 7. `energy_cost` - Filter Nodes by Energy Cost 💰

-   **Description:** Retrieves all UUID nodes with a specific energy cost value.
-   **Request Payload:**
    ```json
    {
      "client_id": "billing_system_interface",
      "request": "energy_cost",
      "data": 0.35
    }
    ```
    -   `data` (Number): The exact energy cost value to match.
-   **Response Topic:** `rust/response/{client_id}/energy_cost`
-   **Success Response:** An array of node objects matching the cost (structure same as `uuid` success response).
-   **Error Response:** Published if `data` is missing, not a number, or the query fails.
-   **Notes:** Uses a read replica (`read_conn_2`).

---

### 8. `energy_consume` - Filter Nodes by Energy Consumption ⚡

-   **Description:** Retrieves all UUID nodes with a specific energy consumption value.
-   **Request Payload:**
    ```json
    {
      "client_id": "efficiency_reporter",
      "request": "energy_consume",
      "data": 2.1
    }
    ```
    -   `data` (Number): The exact energy consumption value to match.
-   **Response Topic:** `rust/response/{client_id}/energy_consume`
-   **Success Response:** An array of node objects matching the consumption (structure same as `uuid` success response).
-   **Error Response:** Published if `data` is missing, not a number, or the query fails.
-   **Notes:** Uses a read replica (`read_conn_2`).

---

### 9. `newest` - Fetch Newest Nodes ✨

-   **Description:** Retrieves the UUIDs of the 50 most recent nodes based on their timestamp.
-   **Request Payload:**
    ```json
    {
      "client_id": "latest_updates_feed",
      "request": "newest"
      // No 'payload' or 'data' needed
    }
    ```
-   **Response Topic:** `rust/response/{client_id}/newest`
-   **Success Response:**
    ```json
    [
      "uuid-most-recent",
      "uuid-second-most-recent",
      // ... up to 50 UUID strings
    ]
    ```
    -   Returns an array of UUID strings.
-   **Error Response:** Published if the query fails.
-   **Notes:** Uses a read replica (`read_conn_1`). Returns only UUIDs, not full node details.

---

### 10. `add` - Add/Update Nodes and Relationships ➕

-   **Description:** Creates new nodes and relationships in the database based on the provided data. If a node with the same UUID already exists, it *might* be updated (behavior depends on the underlying `create_new_relation` Cypher query logic - currently it seems to skip existing UUIDs for creation but merges relationships).
-   **Request Payload:**
    ```json
    {
      "client_id": "data_ingestion_service",
      "request": "add",
      "data": { // Note: The outer object contains the 'data' key
        "data": [ // The actual data is in an inner array also keyed 'data'
          {
            "uuid": "new-uuid-1",
            "color": "purple",
            "sensor_data": { "temperature": 19.5, "humidity": 55.0 },
            "timestamp": "2025-04-25T14:00:00Z",
            "energy_consume": 0.8,
            "energy_cost": 0.15
          },
          {
            "uuid": "new-uuid-2",
            "color": "orange",
            "sensor_data": { "temperature": 20.0, "humidity": 54.3 },
            "timestamp": "2025-04-25T14:05:00Z",
            "energy_consume": 0.9,
            "energy_cost": 0.16
          }
          // ... more data items
        ]
      }
    }
    ```
    -   `data`: An object that **must** contain a `data` key, which holds an array of node data objects.
    -   Each object in the inner `data` array should conform to the validation rules in crud.rs (requires `uuid`, `color`, `sensor_data` object with `temperature` and `humidity`, `timestamp`, `energy_consume`, `energy_cost`).
-   **Response Topic:** `rust/response/{client_id}/add`
-   **Success Response:**
    ```json
    // If nodes/relations were created/merged
    {
      "status": "success",
      "message": "Nodes/relations successfully added/updated"
    }

    // If no new nodes were created (e.g., all UUIDs existed)
    {
      "status": "no_change",
      "message": "No new nodes or relations were created (data might already exist or represent an update)"
    }
    ```
-   **Error Response:** Published if `data` is missing, validation fails, serialization fails, or the database query fails. Includes an error message.
-   **Notes:** Uses the primary write instance (`write_conn`). Performs data validation before attempting insertion.

---

### 11. `relation` - Export Nodes with Relationships 🕸️

-   **Description:** Exports a portion of the graph, specifically nodes and their direct relationships, in a JSON format suitable for visualization or analysis. Currently limited to 1000 paths.
-   **Request Payload:**
    ```json
    {
      "client_id": "graph_visualizer_tool",
      "request": "relation"
      // No 'payload' or 'data' needed
    }
    ```
-   **Response Topic:** `rust/response/{client_id}/relation`
-   **Success Response:** A JSON array representing the paths (nodes and relationships) as converted by Neo4j's `apoc.convert.toJson`. The exact structure depends on the APOC procedure's output. It will likely be a complex nested structure.
    ```json
    // Example structure (simplified)
    [
      { /* Path 1 representation */ },
      { /* Path 2 representation */ },
      // ... up to 1000 paths
    ]
    ```
    - Returns an empty array `[]` if no relationships are found.
-   **Error Response:** Published if the query fails or the result parsing fails.
-   **Notes:** Uses a read replica (`read_conn_1`). Relies on the APOC library being installed in Neo4j. The limit is hardcoded (1000).

---

### 12. `page` - Fetch Paginated Nodes 📖

-   **Description:** Retrieves a specific page of UUID nodes, ordered by timestamp descending. Useful for handling large datasets without requesting everything at once.
-   **Request Payload:**
    ```json
    {
      "client_id": "paginated_table_view",
      "request": "page",
      "data": 2 // Requesting page number 2
    }
    ```
    -   `data` (Number): The page number to retrieve (1-based index). Page 1 is the first page.
-   **Response Topic:** `rust/response/{client_id}/page`
-   **Success Response:**
    ```json
    {
      "nodes": [
        { /* Node object */ },
        { /* Node object */ }
        // ... up to PAGE_SIZE nodes (currently 25)
      ],
      "pagination": {
        "total_count": 1234, // Total number of nodes
        "total_pages": 50,   // Total number of pages
        "current_page": 1,   // The page number returned (0-based index internally, so requested page 2 -> current_page 1)
        "page_size": 25      // Number of items per page
      }
    }
    ```
    -   `nodes`: An array of node objects for the requested page.
    -   `pagination`: An object containing metadata about the pagination.
-   **Error Response:** Published if `data` is missing, not a positive integer, or the query fails.
-   **Notes:** Uses a read replica (`read_conn_2`). The page size is fixed internally (currently 25). Page numbers in the request are 1-based, but the `current_page` in the response reflects the internal 0-based index used for calculation.

---

### 13. `delete` - Delete Specific Node(s) 🗑️

-   **Description:** Deletes one or more nodes (and potentially related orphaned data like `Color`, `Temperature` nodes if they become detached) based on their UUIDs.
-   **Request Payload:**
    ```json
    {
      "client_id": "admin_cleanup_tool",
      "request": "delete",
      "data": [
        "uuid-to-delete-1",
        "uuid-to-delete-2"
      ]
    }
    ```
    -   `data`: An array of UUID strings identifying the nodes to be deleted. An empty array `[]` is valid and will result in no deletion.
-   **Response Topic:** `rust/response/{client_id}/delete`
-   **Success Response:**
    ```json
    // If nodes were deleted
    {
      "status": "success",
      "message": "Successfully deleted 2 node(s).",
      "deleted_count": 2
    }

    // If no matching nodes were found
    {
      "status": "not_found",
      "message": "No nodes found matching the provided UUIDs.",
      "deleted_count": 0
    }

    // If an empty array was sent
     {
        "status": "success",
        "message": "Received empty list, no nodes deleted.",
        "deleted_count": 0
     }
    ```
-   **Error Response:** Published if `data` is missing, not an array, contains non-string elements, or the database query fails.
-   **Notes:** Uses the primary write instance (`write_conn`). The deletion logic attempts to clean up related nodes (like `Color`, `Temperature`, etc.) *only* if they become completely orphaned (no other nodes link to them) after the UUID node is deleted.

---

### 14. `topic` - (Not Implemented) 🚧

-   **Description:** This request type is recognized but currently not implemented.
-   **Request Payload:**
    ```json
    {
      "client_id": "future_feature_client",
      "request": "topic"
      // Potentially other fields, but irrelevant as it's not implemented
    }
    ```
-   **Response Topic:** `rust/response/{client_id}/topic`
-   **Response:**
    ```json
    {
      "status": "not_implemented",
      "message": "Topic request handling is not implemented"
    }
    ```

---

## ⚠️ Error Handling

-   **JSON Parsing Errors:** If the incoming payload is not valid JSON, an error is logged, and processing stops for that message. No MQTT error response is sent in this specific case as the structure is fundamentally broken.
-   **Missing `client_id`:** An error is logged, and processing stops. No MQTT error response can be sent as the destination is unknown.
-   **Missing `request`:** An error is logged, and an error response is published to `rust/response/{client_id}` indicating the missing field.
-   **Invalid Payload/Data:** For requests requiring specific `payload` or `data`, if the field is missing or has the wrong type/structure, an error response detailing the issue is published to `rust/response/{client_id}/error` (or a specific error topic if defined).
-   **Database Errors:** If a Neo4j query fails during execution, an error is logged, and an error response is published, usually indicating a failure to perform the requested database operation.
-   **Unknown Request Type:** If the `request` field contains an unrecognized value, a warning is logged, and an error response is published to `rust/response/{client_id}` indicating the unknown request type.

Error responses generally follow this structure:

```json
// Published to rust/response/{client_id}/error or similar
{
  "status": "error",
  "request_type": "the_original_request_type", // e.g., "uuid", "add"
  "error": "A message describing the error"
}
```

## 🧩 Dependencies

The request processor relies heavily on:

-   `db::DatabaseCluster`: To get connections to the appropriate read/write database instances.
-   `db_operations::*`: Modules containing the actual logic for interacting with Neo4j (CRUD operations, specific queries, exports).
-   `mqtt::publisher`: Functions (`publish_result`, `publish_error_response`) used to send responses back via MQTT.
-   `serde_json`: For parsing incoming JSON and serializing outgoing responses.
-   `rumqttc`: The MQTT client library.
-   `log`: For logging information, warnings, and errors.

