# Go back home [🏠](../Database.md)

# TCP Client for Rust Server 🚀

This document describes a Python script (`tcp_communication_example.py`) designed to interact with a Rust TCP server. It covers the script's features, how to use it, and the underlying communication protocol for sending requests to the server.

## ✨ Features

*   **TCP Connection Management:** Establishes and manages a TCP socket connection to the specified server host and port. 🔌
*   **Password Authentication:** Handles the initial password authentication required by the server. 🔑
*   **JSON Communication:** Sends data formatted as JSON strings and receives/parses JSON responses from the server. 📄
*   **Structured Request Types:** Supports sending different types of requests identified by a `type` field in the JSON payload (`message`, `command`, `data`). ✉️ ⚙️ 📊
*   **Initial Data Loading:** Can automatically load and send JSON data from a `test.json` file upon successful connection and authentication. 📂
*   **Interactive Mode:** Provides a command-line menu for interactively sending different types of messages or custom JSON payloads to the server. ⌨️
*   **Response Handling:** Receives responses, parses them, and prints formatted output indicating success or error status. ✅ ❌
*   **Graceful Shutdown:** Closes the TCP connection cleanly when exiting. 👋

## 🛠️ Usage

1.  **Prerequisites:**
    *   Ensure you have Python 3 installed on your system.
    *   The Rust TCP server (which this client connects to) must be running and accessible on the network (default: `localhost:12345`).
    *   (Optional) A file named `test.json` should exist in the same directory as the script if you want to send initial data automatically. This file should contain a valid JSON object.

2.  **Running the Script:**
    *   Open your terminal or command prompt.
    *   Navigate to the directory containing `tcp_communication_example.py`.
    *   Run the script using the Python interpreter:
        ```bash
        python tcp_communication_example.py
        ```

3.  **Authentication:**
    *   The script will attempt to connect to the server.
    *   If successful, the server will likely send a password prompt (e.g., "Password:").
    *   The script automatically sends the hardcoded password (`1234` in the example - **remember to change this in a real application!**).
    *   The server will respond with an authentication status message.

4.  **Initial Data Send (Optional):**
    *   If authentication succeeds and `test.json` is found and valid, the script will send its contents to the server.

5.  **Interactive Menu:**
    *   After the initial steps, you'll see a menu:
        ```
        --- Options ---
        1. Send message (type: 'message')
        2. Send command (type: 'command')
        3. Send custom JSON
        4. Exit
        Choose an option (1-4):
        ```
    *   Enter the number corresponding to the action you want to perform:
        *   **1:** Prompts you to enter message content. Sends a JSON with `{"type": "message", "content": "your_message"}`.
        *   **2:** Prompts you to enter a command string. Sends a JSON with `{"type": "command", "command": "your_command"}`.
        *   **3:** Prompts you to enter a complete JSON string. Useful for sending `data` types or other custom structures.
        *   **4:** Closes the connection and exits the script.

6.  **Server Responses:**
    *   After sending any data, the script waits for a response from the server.
    *   Responses are expected to be JSON objects with `status` (`success` or `error`) and `message` fields. The script prints these responses to the console, color-coded for clarity. 💚❤️

## 📡 Server Communication Protocol (General)

This section describes how any client (not just the Python example) should communicate with the Rust server.

1.  **Transport:** Communication occurs over **TCP/IP**. The client initiates a connection to the server's IP address and port.
2.  **Authentication:**
    *   Upon connection, the server typically sends a password prompt (e.g., `Password:`). This prompt might not be terminated by a newline.
    *   The client must send the correct password as a plain UTF-8 string. **Crucially, the client should NOT add a newline character (`\n`) after sending the password.**
    *   The server validates the password and sends back a confirmation message (e.g., `Access granted\n` or `Access denied\n`), terminated by a **newline character (`\n`)**.
3.  **Data Format:** All subsequent communication (after successful authentication) uses **JSON** objects.
4.  **Message Framing:**
    *   The client sends a complete JSON object as a UTF-8 encoded string.
    *   **Important:** The client **does not** add a newline (`\n`) after sending its JSON request.
    *   The server processes the JSON request.
    *   The server sends back a JSON response string.
    *   **Important:** The server **terminates** its JSON response string with a single **newline character (`\n`)**. Clients must read data from the socket until this newline character is received to ensure they have the complete JSON response.
5.  **Request Structure:** Client requests should be JSON objects containing at least a `type` field to indicate the nature of the request. Common types observed in the Rust handler (`ip_payload_handler.rs`) are:
    *   **`message`**: For sending simple string messages.
        ```json
        {
          "type": "message",
          "content": "Your string message here"
        }
        ```
    *   **`command`**: For instructing the server to perform specific actions.
        ```json
        {
          "type": "command",
          "command": "name_of_the_command"
        }
        ```
        *(Example commands might be `init`, `reset`, `status`, etc., depending on the server's `command_handler::router` implementation)*
    *   **`robotdata`**: Zum Senden vollständiger Datensätze, die in allen drei Datenbank-Shards gespeichert werden sollen.
        *   **Payload-Struktur:** Erwartet ein JSON-Objekt mit einem `type`-Feld (`"robotdata"`) und einem `data`-Feld. Das `data`-Feld muss ein **Array** von Objekten sein. Jedes Objekt im Array repräsentiert einen vollständigen Datensatz und **muss** die folgenden Felder enthalten:
            *   `id`: Eine numerische ID (wird derzeit vom Server ignoriert und durch eine global generierte ID ersetzt).
            *   `uuid`: Eine eindeutige String-ID.
            *   `color`: Ein String, der die Farbe repräsentiert.
            *   `sensor_data`: Ein Objekt, das die Sensordaten enthält:
                *   `temperature`: Eine Fließkommazahl für die Temperatur.
                *   `humidity`: Eine Fließkommazahl für die Luftfeuchtigkeit.
            *   `timestamp`: Ein String, der den Zeitstempel repräsentiert (z. B. im ISO 8601-Format).
            *   `energy_consume`: Eine Fließkommazahl für den Energieverbrauch.
            *   `energy_cost`: Eine Fließkommazahl für die Energiekosten.
        *   **Funktionsweise:** Der Server validiert jedes Objekt im `data`-Array. Für jedes gültige Objekt wird eine neue globale ID generiert. Anschließend werden die entsprechenden Daten über die drei Shards verteilt und gespeichert (`create_new_nodes` in `sharding.rs`).
        *   **Beispiel:**
            ```json
            {
              "type": "robotdata",
              "data": [
                {
                  "uuid": "robot-uuid-xyz",
                  "color": "red",
                  "sensor_data": {
                    "temperature": 25.5,
                    "humidity": 55.2
                  },
                  "timestamp": "2025-04-30T10:00:00Z",
                  "energy_consume": 1.2,
                  "energy_cost": 0.15
                }
                // Weitere Objekte können hier folgen
              ]
            }
            ```
        *   **Wichtige Hinweise:**
            *   Das `data`-Feld **muss** ein Array sein, auch wenn nur ein Datensatz gesendet wird.
            *   Alle Felder innerhalb der Objekte im `data`-Array sind **erforderlich** und müssen den korrekten Datentyp haben, sonst schlägt die Validierung fehl (`validate_new_item` in `sharding.rs`).
            *   Die `id` im gesendeten Payload wird nicht verwendet; der Server weist eine eigene, eindeutige globale ID zu.

    *   **`energydata`**: Zum Senden spezifischer Energiedaten, die nur in Shard 3 gespeichert werden sollen.
        *   **Payload-Struktur:** Erwartet ein JSON-Objekt mit einem `type`-Feld (`"energydata"`) und einem `data`-Feld. Das `data`-Feld muss ein **Array** von Objekten sein. Jedes Objekt im Array **muss** die folgenden Felder enthalten:
            *   `timestamp`: Ein String, der den Zeitstempel repräsentiert.
            *   `energy_consume`: Eine Fließkommazahl für den Energieverbrauch.
            *   `energy_cost`: Eine Fließkommazahl für die Energiekosten.
        *   **Funktionsweise:** Der Server validiert jedes Objekt im `data`-Array (`validate_new_energydata` in `sharding.rs`). Für jedes gültige Objekt werden die Daten in Shard 3 gespeichert (`create_new_energy_nodes` in `sharding.rs`). Es wird **keine** globale ID verwendet oder Daten in anderen Shards gespeichert.
        *   **Beispiel:**
            ```json
            {
              "type": "energydata",
              "data": [
                {
                  "timestamp": "2025-04-30T11:00:00Z",
                  "energy_consume": 0.8,
                  "energy_cost": 0.10
                },
                {
                  "timestamp": "2025-04-30T11:05:00Z",
                  "energy_consume": 0.9,
                  "energy_cost": 0.11
                }
              ]
            }
            ```
        *   **Wichtige Hinweise:**
            *   Das `data`-Feld **muss** ein Array sein.
            *   Alle Felder (`timestamp`, `energy_consume`, `energy_cost`) sind **erforderlich**.

    *   **`sensordata`**: Zum Senden spezifischer Sensordaten, die nur in Shard 2 gespeichert werden sollen.
        *   **Payload-Struktur:** Erwartet ein JSON-Objekt mit einem `type`-Feld (`"sensordata"`) und einem `data`-Feld. Das `data`-Feld muss ein **Array** von Objekten sein. Jedes Objekt im Array **muss** die folgenden Felder enthalten:
            *   `timestamp`: Ein String, der den Zeitstempel repräsentiert.
            *   `temperature`: Eine Fließkommazahl für die Temperatur.
            *   `humidity`: Eine Fließkommazahl für die Luftfeuchtigkeit.
        *   **Funktionsweise:** Der Server validiert jedes Objekt im `data`-Array (`validate_new_sensordata` in `sharding.rs`). Für jedes gültige Objekt werden die Daten in Shard 2 gespeichert (`create_new_sensor_nodes` in `sharding.rs`). Es wird **keine** globale ID verwendet oder Daten in anderen Shards gespeichert.
        *   **Beispiel:**
            ```json
            {
              "type": "sensordata",
              "data": [
                {
                  "timestamp": "2025-04-30T12:00:00Z",
                  "temperature": 22.1,
                  "humidity": 60.5
                },
                {
                  "timestamp": "2025-04-30T12:10:00Z",
                  "temperature": 22.3,
                  "humidity": 61.0
                }
              ]
            }
            ```
        *   **Wichtige Hinweise:**
            *   Das `data`-Feld **muss** ein Array sein.
            *   Alle Felder (`timestamp`, `temperature`, `humidity`) sind **erforderlich**.

6.  **Response Structure:** The server typically replies with a JSON object containing:
    *   `status`: A string, either `"success"` or `"error"`.
    *   `message`: A string providing details about the outcome or the error encountered.
    ```json
    // Example Success Response
    {
      "status": "success",
      "message": "Command 'init' executed successfully"
    }

    // Example Error Response
    {
      "status": "error",
      "message": "No 'command' field found in JSON"
    }
    ```

