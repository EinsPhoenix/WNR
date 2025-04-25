# Go back home [🏠](../Database.md)
# MQTT Multi-Client Test Tool 📊🐍

This document provides a comprehensive guide to the `mqtt_multi_client.py` script, designed for testing and benchmarking an MQTT-based Rust server application. It details the script's features, usage instructions, individual components, and the underlying MQTT communication protocol.

## ✨ Features

*   **Multi-Client Simulation:** Run multiple MQTT clients concurrently to simulate load. 👥
*   **Targeted & Random Testing:** Execute specific request types or run random requests across clients. 🎯🎲
*   **Diverse Request Types:** Supports various request types handled by the Rust server (e.g., `uuid`, `all`, `color`, `time_range`, `page`, etc.). ⚙️
*   **Pagination Handling:** Automatically handles large responses split into multiple MQTT messages (paginated responses) and reassembles them. 📄➡️📦
*   **Performance Metrics:** Collects detailed metrics for each client's request, including latency and duration. ⏱️
*   **Benchmarking Report:** Generates a summary report (`.txt`) detailing the performance across all clients. 📈
*   **Individual Client Logging:** Creates separate log files for each client instance for detailed debugging. 📝
*   **Command-Line Interface:** Configurable via command-line arguments. ⌨️
*   **Clear Console Output:** Provides informative status messages with emojis during execution. ✅❌🔔

## 🔧 Prerequisites

1.  **Python:** Python 3.6 or higher installed.
2.  **Paho MQTT Library:** The Python MQTT client library.
3.  **MQTT Broker:** An MQTT broker (like Mosquitto) must be running and accessible. The script defaults to `localhost:1883` and uses credentials `admin`/`admin`. Adjust the constants `BROKER`, `PORT`, `USERNAME`, `PASSWORD` in the script if needed.
4.  **Rust MQTT Server:** The target Rust application (which processes requests from `rust/request`) must be running and connected to the same MQTT broker.

## ⚙️ Installation

Install the required Python library using pip:

```bash
pip install paho-mqtt
```

## ▶️ Running the Script

Execute the script from your terminal.

**Basic Usage (5 clients, random tests):**

```bash
python mqtt_multi_client.py
```

**Specify Number of Clients:**

```bash
python mqtt_multi_client.py --clients 10
```

**Run a Specific Test Type for All Clients:**

```bash
python mqtt_multi_client.py --clients 5 --test all
```

```bash
python mqtt_multi_client.py --clients 3 --test time_range
```

**Command-Line Arguments:**

*   `--clients N`: (Optional) Specifies the number of concurrent clients to run. Defaults to 5. Recommended range: 5-20. Max capped at 50.
*   `--test TEST_TYPE`: (Optional) Specifies the exact request type to run for *all* clients. If omitted, each client picks a random test type. Valid choices are: `uuid`, `all`, `color`, `time_range`, `temperature_humidity`, `timestamp`, `energy_cost`, `energy_consume`, `newest`, `relation`, `page`.

## 📜 Script Structure and Components

The script is organized into a main class (`MqttClient`), helper functions for orchestration, and the main execution block.

### `MqttClient` Class

This class represents a single MQTT client instance responsible for connecting, sending a request, receiving the response (handling pagination), and collecting metrics.

*   **`__init__(self, client_name=None)`**
    *   Initializes a client instance.
    *   Generates a unique `client_id` (e.g., `python-client-xxxxxxxx`) if `client_name` is not provided.
    *   Sets up threading events (`response_received`) and locks (`lock`) for synchronization.
    *   Initializes variables for storing responses (`received_response`), timing (`start_time`, `first_response_time`, `end_time`), pagination state (`paginated_messages`), and metrics flags.
    *   Creates the underlying `paho.mqtt.client.Client`.
    *   Assigns MQTT callbacks (`on_connect`, `on_message`).
    *   Sets broker credentials.
    *   Calls `setup_logging()`.

*   **`setup_logging(self)`**
    *   Configures logging for this specific client instance.
    *   Creates a `logs` directory if it doesn't exist.
    *   Sets up a unique log file named `logs/log_client_{client_id}_{timestamp}.log`.
    *   Logs messages at the `INFO` level and above to the file.

*   **`on_connect(self, client, userdata, flags, rc)`**
    *   MQTT callback triggered when the client attempts to connect to the broker.
    *   Logs and prints whether the connection was successful (`rc == 0`) or failed. ✅❌

*   **`on_message(self, client, userdata, msg)`** 📨
    *   The core MQTT callback triggered when a message is received on a subscribed topic.
    *   Records `first_response_time` if it's the first message received for the current request.
    *   Decodes the message payload from JSON.
    *   **Message Routing:**
        *   Checks if the topic matches the pattern for a paginated message (`/page/{number}`). If yes, calls `handle_paginated_message()`. 📄
        *   Checks if the topic matches the pattern for a pagination summary (`/summary`). If yes, calls `handle_pagination_summary()`. 📋
        *   Otherwise, treats it as a standard, non-paginated response. Stores the payload in `received_response`, records `end_time`, marks the request as completed (`request_completed = True`), checks for `"status": "error"` to set `request_failed`, and signals completion using `self.response_received.set()`.
    *   Handles potential `JSONDecodeError` if the payload is invalid. ⚠️

*   **`handle_paginated_message(self, match, payload)`**
    *   Called by `on_message` for topics like `.../page/1`.
    *   Extracts the base topic and page number from the `match` object.
    *   Extracts the `request_id` from the payload.
    *   Uses a unique `message_id` (combining base topic and `request_id`) to store pagination state in `self.paginated_messages`.
    *   Initializes storage for the `message_id` if it's the first page received.
    *   Stores the `data` array from the payload under the corresponding `page_num`.
    *   Increments the count of `received_pages`.
    *   Logs the progress (e.g., "Received page 2/5...").
    *   If `received_pages` equals `total_pages`, calls `reassemble_paginated_message()` to finalize. 🔄

*   **`handle_pagination_summary(self, topic, payload)`**
    *   Called by `on_message` for topics like `.../summary`.
    *   Extracts `request_id`, `total_pages`, and `topic_base` from the payload.
    *   Constructs the `message_id`.
    *   Logs the summary information.
    *   Checks if all pages for this `message_id` have already been received (based on the count in `self.paginated_messages`). If yes, calls `reassemble_paginated_message()`. This handles cases where the summary arrives after all data pages.

*   **`reassemble_paginated_message(self, message_id)`** 📦
    *   Called when all pages for a paginated message (identified by `message_id`) are received.
    *   Ensures reassembly happens only once using the `complete` flag.
    *   Retrieves all stored page data from `self.paginated_messages[message_id]['pages']`.
    *   Sorts the pages by page number and extends a final list (`all_items`) with the data from each page.
    *   Logs the successful reassembly.
    *   Sets the final `self.received_response` to the `all_items` list.
    *   Records `end_time`, sets `request_completed = True`, checks for errors in the reassembled data, and signals completion via `self.response_received.set()`.
    *   Saves the complete reassembled JSON response to a file (e.g., `paginated_response_{client_id}_{timestamp}.json`). 💾

*   **`send_request(self, query_data, response_suffix, timeout=15)`** 📤
    *   The main method to initiate a request.
    *   Resets state variables (response, timing, pagination, metrics flags).
    *   Connects to the MQTT broker and starts the network loop (`client.loop_start()`).
    *   Determines the specific response topic(s) based on `response_suffix` and `client_id`.
        *   Standard: `rust/response/{client_id}/{response_suffix}`
        *   UUID specific: `rust/uuid/{client_id}`
        *   Pagination: Also subscribes to `.../page/#` (wildcard for all pages) and `.../summary`.
    *   Subscribes to the necessary response topics. 🔔
    *   Injects the `client_id` into the `query_data` payload.
    *   Records the `start_time`.
    *   Publishes the JSON-encoded `query_data` to the main `REQUEST_TOPIC` (`rust/request`).
    *   Waits for the `self.response_received` event to be set (by `on_message` or `reassemble_paginated_message`) or until the `timeout` expires. Uses a longer timeout for potentially large 'all' requests.
    *   Calculates and logs the time to the first response (`first_response_latency`).
    *   Logs whether the request completed successfully or timed out. ⌛
    *   Stops the network loop (`client.loop_stop()`) and disconnects.
    *   Returns the `self.received_response` (which could be a dictionary, a list, or `None` if timed out).

*   **`get_metrics(self)`** -> `Dict[str, Any]`
    *   Returns a dictionary containing all the performance metrics collected during the `send_request` call for this client instance. Includes timings, status flags (completed, timed_out, failed), pagination info, etc.

### Helper Functions

*   **`run_test_client_with_metrics(client_name, request_type, params)`** -> `Tuple[Optional[Any], Dict[str, Any]]`
    *   A wrapper function that:
        *   Creates an `MqttClient` instance.
        *   Uses a dictionary (`request_handlers`) to map `request_type` strings to lambda functions that call `client.send_request` with the correctly formatted payload based on `params`.
        *   Executes the appropriate request handler.
        *   Returns both the result received from the server and the metrics dictionary obtained from `client.get_metrics()`.

*   **`run_multiple_clients(num_clients=5, test_type=None)`**
    *   The main orchestration function.
    *   Defines the list of valid `test_types`.
    *   Creates a list of tasks, where each task is a tuple `(client_name, selected_test, params)`.
        *   If `test_type` is specified, all clients run that test.
        *   Otherwise, a random `selected_test` is chosen for each client.
        *   Generates slightly varied `params` for different clients (e.g., different UUIDs, colors, timestamps) to avoid identical requests.
    *   Uses `concurrent.futures.ThreadPoolExecutor` to run `run_test_client_with_metrics` for each task concurrently in separate threads.
    *   Collects the metrics dictionaries from all completed client runs.
    *   Calls `generate_benchmark_report()` with the collected metrics.

*   **`generate_benchmark_report(metrics)`** 📊
    *   Takes a list of metrics dictionaries (one from each client).
    *   Calculates aggregate statistics: total clients, completed/timed_out/failed counts, average response times, number of paginated vs. non-paginated responses.
    *   Analyzes metrics per request type (count, success rate, average time).
    *   Writes a detailed text report to `logs/benchmark_report_{timestamp}.txt`.
    *   Prints a summary of the report to the console.

### Main Execution Block (`if __name__ == "__main__":`)

*   Uses `argparse` to handle command-line arguments (`--clients`, `--test`).
*   Performs basic validation on the number of clients.
*   Calls `run_multiple_clients()` to start the test run based on the parsed arguments.

## 📡 MQTT Request Protocol (General)

This describes how any MQTT client should interact with the Rust server based on the logic observed in request_processor.rs.

1.  **Connection:**
    *   Connect to the MQTT Broker (e.g., `localhost:1883`).
    *   Provide credentials if required (e.g., `admin`/`admin`).

2.  **Request Topic:**
    *   Publish all requests to the topic: `rust/request`.

3.  **Request Payload (JSON):**
    *   The payload **must** be a valid JSON object.
    *   **Required Fields:**
        *   `client_id` (String): A unique identifier for the client sending the request. The server uses this to route the response back.
        *   `request` (String): Specifies the type of operation requested.
    *   **Conditional Fields (depend on `request` value):**
        *   If `request` is `"uuid"`:
            *   `payload` (Array): An array of objects, where each object must contain a `"uuid"` (String) field.
            *   Example: `{"client_id": "client1", "request": "uuid", "payload": [{"uuid": "abc"}, {"uuid": "def"}]}`
        *   If `request` is `"all"`: No additional fields needed.
            *   Example: `{"client_id": "client2", "request": "all"}`
        *   If `request` is `"color"`:
            *   `data` (String): The color value to query.
            *   Example: `{"client_id": "client3", "request": "color", "data": "blue"}`
        *   If `request` is `"time_range"`:
            *   `start` (String): Start timestamp (RFC3339 format, e.g., "2025-01-01T00:00:00Z").
            *   `end` (String): End timestamp (RFC3339 format).
            *   Example: `{"client_id": "client4", "request": "time_range", "start": "...", "end": "..."}`
        *   If `request` is `"temperature_humidity"`:
            *   `temperature` (Number): Temperature value.
            *   `humidity` (Number): Humidity value.
            *   Example: `{"client_id": "client5", "request": "temperature_humidity", "temperature": 25.5, "humidity": 60.1}`
        *   If `request` is `"timestamp"`:
            *   `data` (String): The specific timestamp to query (RFC3339 format).
            *   Example: `{"client_id": "client6", "request": "timestamp", "data": "2025-02-10T10:00:00Z"}`
        *   If `request` is `"energy_cost"`:
            *   `data` (Number): Minimum energy cost value.
            *   Example: `{"client_id": "client7", "request": "energy_cost", "data": 0.15}`
        *   If `request` is `"energy_consume"`:
            *   `data` (Number): Minimum energy consumption value.
            *   Example: `{"client_id": "client8", "request": "energy_consume", "data": 200.0}`
        *   If `request` is `"newest"`: No additional fields needed.
            *   Example: `{"client_id": "client9", "request": "newest"}`
        *   If `request` is `"add"`:
            *   `data` (JSON Object/Array): The complex JSON structure representing the node(s)/relation(s) to add/update (structure depends on `db_operations::crud::create_new_relation`).
            *   Example: `{"client_id": "client10", "request": "add", "data": {"uuid": "new-uuid", "property": "value", "connects_to": ["existing-uuid"]}}`
        *   If `request` is `"relation"`: No additional fields needed.
            *   Example: `{"client_id": "client11", "request": "relation"}`
        *   If `request` is `"page"`:
            *   `data` (Integer): The 1-based page number to retrieve.
            *   Example: `{"client_id": "client12", "request": "page", "data": 3}`

4.  **Response Topics (Subscription):**
    *   Before sending a request, the client **must** subscribe to the topic(s) where it expects the response.
    *   **Standard/Error Response Topic:** `rust/response/{client_id}/{request_type}` (e.g., `rust/response/client3/color`)
    *   **UUID Response Topic:** `rust/uuid/{client_id}` (Note the different structure for UUID requests).
    *   **Pagination Topics (Subscribe to BOTH if expecting potentially large responses):**
        *   `rust/response/{client_id}/{request_type}/page/#` (Wildcard subscription for all pages)
        *   `rust/response/{client_id}/{request_type}/summary` (Subscription for the summary message)

5.  **Response Payload Format (JSON):**
    *   **Standard/Error:** Typically a JSON object. May contain the requested data directly or status information. Error responses usually follow the pattern:
        ```json
        {
          "status": "error",
          "message": "Error description here"
        }
        ```
        Success responses for operations like "add" might look like:
        ```json
        {
          "status": "success",
          "message": "Nodes/relations successfully added/updated"
        }
        ```
        Or for queries, it might be an array of results or a specific object.
    *   **Paginated Responses:** If a response is too large, it will be split:
        *   **Page Messages:** Published to `.../page/{page_number}`. Payload format:
            ```json
            {
              "type": "paginated",
              "request_id": "unique-guid-for-this-request",
              "page": 1, // Current page number
              "total_pages": 5, // Total pages for this request
              "data": [ /* Array of data items for this page */ ]
            }
            ```
        *   **Summary Message:** Published to `.../summary` *after* all page messages. Payload format:
            ```json
            {
              "type": "summary",
              "request_id": "unique-guid-for-this-request", // Same as in pages
              "total_items": 1234, // Total items across all pages
              "total_pages": 5, // Total pages (same as in pages)
              "original_size": 50000, // Original payload size in bytes
              "topic_base": "rust/response/client11/relation" // The base topic used
            }
            ```
        *   Clients need to collect all `data` arrays from the page messages associated with a `request_id` and reassemble them into the final result list. The summary message confirms the total number of pages expected.

