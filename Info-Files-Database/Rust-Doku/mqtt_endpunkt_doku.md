# Go back home [🏠](../Database.md)
# 📄 MQTT Request Processor Documentation

This document outlines the functionality of the `request_processor.rs` module, which acts as the central hub for handling incoming MQTT requests within the `datacenter` application. It parses requests, interacts with the Neo4j database cluster (using read replicas and a primary write instance), and publishes results or errors back via MQTT. 🚀

---

## 📬 General Request Structure

All requests sent to the `datacenter` via MQTT on the `rust/requests` topic **must** adhere to the following JSON structure:

```json
{
  "client_id": "your_unique_client_identifier",
  "request": "the_specific_request_type",
  "payload": { ... }
}
```

### Required Fields
- **`client_id`** (String, **Required**): A unique identifier for the client sending the request. This ID is crucial as it's used to route the response back to the correct MQTT topic.
- **`request`** (String, **Required**): Specifies the type of operation the client wants to perform. The available request types are detailed below.

### Optional Fields
- **`payload`** (Varies): Contains the necessary data for the specific request. The structure of this field depends on the `request` type.

---

## 📡 API Endpoints (MQTT Request Types)

The processor listens on the `rust/requests` topic. Responses are published to specific topics based on the `client_id` and `request` type. Error responses are generally published to `rust/response/{client_id}/error`.

---

### 1. `uuid` - Fetch Specific Node(s) 🆔

- **Description:** Retrieves the details of one or more specific nodes based on their UUIDs.
- **Request Payload:**
  ```json
  {
    "client_id": "frontend_dashboard_1",
    "request": "uuid",
    "payload": [
      { "uuid": 12345 },
      { "uuid": 67890 }
    ]
  }
  ```
  - **`payload`**: An array of objects, where each object **must** contain a `uuid` (Number) key.
- **Response Topic:** `rust/uuid/{client_id}` (A separate message is published for *each* UUID requested).
- **Success Response (per UUID):**
  ```json
  {
    "uuid": 12345,
    "found": true,
    "data": { /* Node data */ }
  }
  ```
  - If not found:
  ```json
  {
    "uuid": 12345,
    "found": false,
    "message": "No data found for this UUID"
  }
  ```
- **Error Response:** Published if the `payload` is missing or not an array.

---

### 2. `all` - Fetch All Nodes 🌍

- **Description:** Retrieves details for *all* UUID nodes stored in the database, ordered by timestamp descending.
- **Request Payload:**
  ```json
  {
    "client_id": "data_exporter_service",
    "request": "all"
  }
  ```
  - No `payload` or `data` needed.
- **Response Topic:** `rust/response/{client_id}/all`
- **Success Response:**
  ```json
  [
    { /* Node 1 data */ },
    { /* Node 2 data */ }
  ]
  ```
- **Error Response:** Published if the database query fails.

---

### 3. `color` - Filter Nodes by Color 🎨

- **Description:** Retrieves all UUID nodes that have a specific color.
- **Request Payload:**
  ```json
  {
    "client_id": "color_analyzer_app",
    "request": "color",
    "data": "red"
  }
  ```
  - **`data`**: The color (String) to filter by.
- **Response Topic:** `rust/response/{client_id}/color`
- **Success Response:** An array of node objects matching the color.
- **Error Response:** Published if `data` is missing, not a string, or the query fails.

---

### 4. `time_range` - Filter Nodes by Time Range ⏳

- **Description:** Retrieves all UUID nodes whose timestamp falls within a specified start and end time.
- **Request Payload:**
  ```json
  {
    "client_id": "history_viewer_01",
    "request": "time_range",
    "start": "2025-04-25T09:00:00Z",
    "end": "2025-04-25T12:00:00Z"
  }
  ```
  - **`start`** (String): The start timestamp (inclusive, ISO 8601 format recommended).
  - **`end`** (String): The end timestamp (inclusive, ISO 8601 format recommended).
- **Response Topic:** `rust/response/{client_id}/time_range`
- **Success Response:** An array of node objects within the time range.
- **Error Response:** Published if `start` or `end` are missing, not strings, or the query fails.

---

### 5. `temperature_humidity` - Filter Nodes by Sensor Values 🌡️💧

- **Description:** Retrieves all UUID nodes matching specific temperature and humidity values.
- **Request Payload:**
  ```json
  {
    "client_id": "sensor_monitor_widget",
    "request": "temperature_humidity",
    "temperature": 25.0,
    "humidity": 60.5
  }
  ```
  - **`temperature`** (Number): The exact temperature value to match.
  - **`humidity`** (Number): The exact humidity value to match.
- **Response Topic:** `rust/response/{client_id}/temperature_humidity`
- **Success Response:** An array of node objects matching the criteria.
- **Error Response:** Published if `temperature` or `humidity` are missing, not numbers, or the query fails.

---

### 6. `timestamp` - Get Sensor Data at Specific Time ⏱️

- **Description:** Retrieves the temperature and humidity recorded exactly at a specific timestamp.
- **Request Payload:**
  ```json
  {
    "client_id": "realtime_graph_component",
    "request": "timestamp",
    "data": "2025-04-25T10:30:15Z"
  }
  ```
  - **`data`** (String): The exact timestamp to query (ISO 8601 format recommended).
- **Response Topic:** `rust/response/{client_id}/timestamp`
- **Success Response:**
  ```json
  {
    "timestamp": "2025-04-25T10:30:15Z",
    "temperature": 23.1,
    "humidity": 48.9
  }
  ```
  - If no data found:
  ```json
  {
    "timestamp": "2025-04-25T10:30:15Z",
    "found": false,
    "message": "No temperature/humidity data found for this timestamp"
  }
  ```
- **Error Response:** Published if `data` is missing, not a string, or the query fails.

---

### 7. `id_energy_cost` - Filter Nodes by Energy Cost 💰

- **Description:** Retrieves all UUID nodes with a specific energy cost value.
- **Request Payload:**
  ```json
  {
    "client_id": "billing_system_interface",
    "request": "id_energy_cost",
    "data": 0.35
  }
  ```
  - **`data`** (Number): The exact energy cost value to match.
- **Response Topic:** `rust/response/{client_id}/energy_cost`
- **Success Response:** An array of node objects matching the cost.
- **Error Response:** Published if `data` is missing, not a number, or the query fails.

---

### 8. `id_energy_consume` - Filter Nodes by Energy Consumption ⚡

- **Description:** Retrieves all UUID nodes with a specific energy consumption value.
- **Request Payload:**
  ```json
  {
    "client_id": "efficiency_reporter",
    "request": "id_energy_consume",
    "data": 2.1
  }
  ```
  - **`data`** (Number): The exact energy consumption value to match.
- **Response Topic:** `rust/response/{client_id}/energy_consume`
- **Success Response:** An array of node objects matching the consumption.
- **Error Response:** Published if `data` is missing, not a number, or the query fails.

---

### 9. `addrobotdata` - Add/Update Nodes and Relationships ➕

- **Description:** Creates new nodes and relationships in the database based on the provided data.
- **Request Payload:**
  ```json
  {
    "client_id": "data_ingestion_service",
    "request": "addrobotdata",
    "data": [
      {
        "uuid": "new-uuid-1",
        "color": "purple",
        "sensor_data": { "temperature": 19.5, "humidity": 55.0 },
        "timestamp": "2025-04-25T14:00:00Z",
        "energy_consume": 0.8,
        "energy_cost": 0.15
      }
    ]
  }
  ```
  - **`data`**: An array of node data objects.
- **Response Topic:** `rust/response/{client_id}/add/robotdata`
- **Success Response:**
  ```json
  {
    "status": "success",
    "message": "Successfully processed 1 nodes/relations",
    "count": 1
  }
  ```
- **Error Response:** Published if `data` is missing, validation fails, or the database query fails.

---

## ⚠️ Error Handling

Error responses generally follow this structure:

```json
{
  "status": "error",
  "message": "A message describing the error"
}
```

---

## 🧩 Dependencies

The request processor relies on:
- `db::DatabaseCluster`
- `db_operations::*`
- `mqtt::publisher`
- `serde_json`
- `rumqttc`
- `log`
