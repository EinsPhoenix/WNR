# MQTT Server Implementation - Documentation

## 📌 Overview

This Rust implementation provides an MQTT server that handles various request types, processes them using a database backend, and returns responses with support for large payload pagination.

## ✨ Features

- **Multiple Request Types**: 12 different request types supported
- **Pagination**: Automatic handling of large responses (>8KB)
- **Database Integration**: Works with a database cluster (read/write separation)
- **Heartbeat Monitoring**: Regular status updates
- **Error Handling**: Comprehensive error responses
- **Asynchronous Processing**: Efficient request handling with Tokio

## 🚀 Quick Start

1. **Configure environment variables**:
   ```bash
   export MQTT_BROKER="mosquitto-broker"
   export MQTT_PORT="1883"
   export MQTT_USER="admin"
   export MQTT_PASSWORD="admin"
   ```

2. **Run the server**:
   ```bash
   cargo run --bin mqtt_server
   ```

## 🔧 Configuration

| Environment Variable | Default Value     | Description                          |
|----------------------|-------------------|--------------------------------------|
| `MQTT_BROKER`        | `mosquitto-broker`| MQTT broker address                  |
| `MQTT_PORT`          | `1883`            | MQTT broker port                     |
| `MQTT_USER`          | `admin`           | MQTT username                        |
| `MQTT_PASSWORD`      | `admin`           | MQTT password                        |

## 📋 Available Request Types

| Request Type            | Description                                                                 | Required Fields                          |
|-------------------------|-----------------------------------------------------------------------------|------------------------------------------|
| `uuid`                  | Get specific node by UUID                                                   | `payload: [{ "uuid": "..." }]`           |
| `all`                   | Get all available data (automatically paginated if large)                  | None                                     |
| `color`                 | Get nodes filtered by color                                                 | `data: "color_name"`                     |
| `time_range`            | Get nodes within a time range                                               | `start: "ISO8601", end: "ISO8601"`       |
| `temperature_humidity`  | Get nodes with specific temperature/humidity                               | `temperature: float, humidity: float`    |
| `timestamp`             | Get temperature/humidity at specific timestamp                             | `data: "ISO8601"`                        |
| `energy_cost`           | Get nodes with specific energy cost                                        | `data: float`                            |
| `energy_consume`        | Get nodes with specific energy consumption                                 | `data: float`                            |
| `newest`                | Get newest nodes                                                           | None                                     |
| `relation`              | Get nodes with relationships (limited to 1000 by default)                 | None                                     |
| `page`                  | Get paginated data (specific page)                                        | `data: page_number`                      |
| `add`                   | Create new nodes/relations                                                | `data: { ...node data... }`              |

## 📊 Response Handling

### Pagination System

Responses larger than 8KB are automatically paginated with:

1. **Page Messages**: Individual pages published to `{topic}/page/{number}`
   ```json
   {
     "type": "paginated",
     "request_id": "UUID",
     "page": 1,
     "total_pages": 3,
     "data": [...]
   }
   ```

2. **Summary Message**: Published to `{topic}/summary`
   ```json
   {
     "type": "summary",
     "request_id": "UUID",
     "total_items": 150,
     "total_pages": 3,
     "original_size": 12000,
     "topic_base": "original/topic"
   }
   ```

### Error Responses

Standard error format:
```json
{
  "status": "error",
  "message": "Description of error"
}
```

## 🏗️ Architecture

```mermaid
graph TD
    A[MQTT Client] -->|Publish| B[rust/request]
    B --> C[MQTT Server]
    C --> D[Database Cluster]
    D --> C
    C -->|Publish| E[rust/response/{client_id}/{type}]
    C -->|Publish| F[rust/status]
```

## 📈 Performance Characteristics

| Metric                | Value/Description                          |
|-----------------------|--------------------------------------------|
| Max Message Size      | 8KB (configurable via `MAX_MESSAGE_SIZE`) |
| Heartbeat Interval    | 60 seconds                                 |
| Connection Timeout    | 20 seconds                                 |
| QoS Level             | AtLeastOnce                                |
| Thread Model          | Tokio async runtime                        |

## 💡 Example Requests

1. **Get specific UUID**:
   ```json
   {
     "client_id": "test-client-1",
     "request": "uuid",
     "payload": [{ "uuid": "abc123xyz001" }]
   }
   ```

2. **Get time range data**:
   ```json
   {
     "client_id": "test-client-1",
     "request": "time_range",
     "start": "2025-01-01T00:00:00Z",
     "end": "2025-03-01T00:00:00Z"
   }
   ```

3. **Add new nodes**:
   ```json
   {
     "client_id": "test-client-1",
     "request": "add",
     "data": {
       "uuid": "new-node-001",
       "properties": {
         "color": "blue",
         "temperature": 22.5
       }
     }
   }
   ```

## ⚠️ Important Notes

1. **Client ID Required**: All requests must include a `client_id` field
2. **Database Connections**: Uses separate read/write connections
3. **Large Responses**: Responses >8KB automatically paginated
4. **Error Handling**: Always check response for `status` field
5. **Heartbeat**: Monitor `rust/status` for server availability

## 📜 License

This implementation is provided as-is under the MIT License.

---

## 🔍 Detailed Function Documentation

### `publish_paginated_results()`

Handles large responses by splitting into pages.

**Parameters**:
- `client`: MQTT AsyncClient
- `topic`: Base topic for responses
- `payload`: Data to publish

**Behavior**:
1. Checks payload size against `MAX_MESSAGE_SIZE`
2. If under limit, publishes directly
3. If over limit:
   - Generates unique request ID
   - Calculates pagination metadata
   - Publishes individual pages
   - Publishes summary message

### `process_request()`

Main request processing function.

**Flow**:
1. Parses incoming request
2. Validates required fields
3. Routes to appropriate handler
4. Publishes response or error
5. Handles database connections

### `start_mqtt_client()`

Server initialization and main loop.

**Phases**:
1. **Connection**: Establishes MQTT connection with timeout
2. **Subscription**: Subscribes to request topic
3. **Heartbeat**: Starts status publishing task
4. **Main Loop**: Processes incoming requests

## 🛠️ Troubleshooting

| Symptom                      | Possible Cause                          | Solution                                |
|------------------------------|----------------------------------------|-----------------------------------------|
| Connection timeout           | Broker unavailable/wrong credentials   | Check broker status and credentials     |
| Missing responses            | Client ID mismatch                     | Verify client_id in request/response    |
| Partial paginated responses  | Network issues                         | Implement client-side reassembly logic  |
| Database errors              | Connection pool exhausted              | Increase database connections           |