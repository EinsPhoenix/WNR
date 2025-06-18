# Quick Guide MQTT

### How does it work?
Forget almost everything you think you know about MQTT. In this system, you have one primary topic where you can request information ('rust/request'). You send your JSON request to this topic to get the data you need—think of it like a REST API, where 'rust/request' is the endpoint for your POST/GET requests. There's also another topic where you can get live data: 'rust/response/livedata'.

### Important Notes on Pagination:
If a response is too large to be sent in a single MQTT message (default limit approx. 8KB in `publisher.rs`), it will be split:
1.  You will receive messages on the topic `rust/response/{client_id}/{request}/page/{page_number}`.
    *   Each of these messages will have `"type": "paginated"` in the JSON.
    *   They will contain `"request_id"`, `"page"` (current page), and `"total_pages"`.
2.  Additionally, a final message will be sent on `rust/response/{client_id}/{request}/summary`.
    *   This will have `"type": "summary"` and provide info like `"total_items"`, `"total_pages"`, and the `"request_id"`.

This allows you to receive and process large datasets piece by piece.

### Live Data
IMPORTANT: The topic for live data is `rust/response/livedata`.

live data can look for example like this:

```json

"count": 2,
  "data": [
    {
      "color": "blue",
      "energy_consume": 0.3,
      "energy_cost": 0.007,
      "sensor_data": {
        "humidity": 60,
        "temperature": 22.1
      },
      "timestamp": "2025-03-10 14:30:00",
      "uuid": "test-uuid-1"
    },
    {
      "color": "green",
      "energy_consume": 0.25,
      "energy_cost": 0.006,
      "sensor_data": {
        "humidity": 55,
        "temperature": 19.8
      },
      "timestamp": "2025-03-10 15:00:00",
      "uuid": "test-uuid-2"
    }
  ],
  "source": "tcp",
  "timestamp": "2025-05-16T08:35:42.721853200+00:00",
  "type": "robotdata"
}

```
### Request Topics
When you need specific data, send a JSON request to `rust/request`. The server will reply on `rust/response/{client_id}/{request}`. For example, here's a basic JSON to get all data from the server:

```json
{
    "request": "all",
    "client_id": "client-1" // You must set this
}
```
The response, in this case, would be on the topic `rust/response/client-1/all/`.

There are more types of requests:

1.  Time range requests (returns nodes within the specified range):
    ```json
    {
        "request": "time_range",
        "start": "2025-01-01T00:00:00Z",
        "end": "2025-03-01T00:00:00Z",
        "client_id": "client-1"
    }
    ```
    Response on `rust/response/client-1/time_range`:
    ```json
    {
        "type": "paginated", // Can be paginated if there's a lot of data!
        "request_id": "some-unique-request-id",
        "page": 1,
        "total_pages": 3, // Example: 3 pages in total
        "data": [
            {
                "id": 123,
                "timestamp": "2025-01-15T10:00:00Z",
                "property1": "value1"
                // ... other node data
            }
            // ... more nodes in this time range (up to pagination limit)
        ]
    }
    // If paginated, further messages will arrive on rust/response/client-1/time_range/page/2, etc.
    // and a summary on rust/response/client-1/time_range/summary
    ```

2.  Temperature and Humidity (returns nodes matching **both** parameters):
    ```json
    {
        "request": "temperature_humidity",
        "temperature": 22.5,
        "humidity": 45.0,
        "client_id": "client-1"
    }
    ```
    Response on `rust/response/client-1/temperature_humidity`:
    ```json
    [ // Can also be paginated!
        {
            "id": 456,
            "temperature": 22.5,
            "humidity": 45.0
            // ... other node data
        }
    ]
    // For pagination: Similar to time_range, with /page/N and /summary endpoints.
    ```

3.  Get all data:
    ```json
    {
        "request": "all",
        "client_id": "client-1"
    }
    ```
    Response on `rust/response/client-1/all`:
    **ATTENTION:** This response is very likely to be paginated!
    ```json
    // First page:
    {
        "type": "paginated",
        "request_id": "unique-all-data-id",
        "page": 1,
        "total_pages": 50, // Example
        "data": [
            { "id": 1, "property": "value" /* ... */ },
            { "id": 2, "property": "value" /* ... */ }
            // ... many more nodes
        ]
    }
    // Further pages on: rust/response/client-1/all/page/2, ... , rust/response/client-1/all/page/50
    // Summary on: rust/response/client-1/all/summary
    // {
    //     "type": "summary",
    //     "request_id": "unique-all-data-id",
    //     "total_items": 2500, // Example
    //     "total_pages": 50,
    //     "original_size": 123456, // Size of the original total payload in bytes
    //     "topic_base": "rust/response/client-1/all"
    // }
    ```

4.  Get data by specific UUID:
    ```json
    {
        "request": "uuid",
        "client_id": "client-1",
        "data": [ // A list of UUIDs you want to query
            { "uuid": 12345 },
            { "uuid": 67890 }
        ]
    }
    ```
    Response on `rust/uuid/client-1`:
    A separate message is sent for each UUID in the request.
    ```json
    // For UUID 12345 (if found):
    {
        "uuid": 12345,
        "found": true,
        "id": 12345, // Neo4j internal ID
        "name": "Sensor A",
        "type": "TemperatureSensor"
        // ... other properties of the node
    }
    ```
    ```json
    // For UUID 67890 (if not found):
    {
        "uuid": 67890,
        "found": false,
        "message": "No data found for this UUID: Some error or not found"
    }
    ```

5.  Filter nodes by color:
    ```json
    {
        "request": "color",
        "client_id": "client-1",
        "data": "blue" // The desired color as a string
    }
    ```
    Response on `rust/response/client-1/color`:
    ```json
    [ // Can be paginated!
        { "id": 777, "color": "blue", "name": "Blue Robot Arm" /* ... */ }
        // ... other nodes with this color
    ]
    // For pagination: Similar to time_range.
    ```

6.  Temperature/Humidity at a specific timestamp:
    ```json
    {
        "request": "timestamp",
        "client_id": "client-1",
        "data": "2025-02-15T12:30:00Z" // Exact timestamp
    }
    ```
    Response on `rust/response/client-1/timestamp`:
    ```json
    {
        "timestamp": "2025-02-15T12:30:00Z",
        "temperature": 21.7,
        "humidity": 48.2
    }
    // Or if nothing was found:
    // {
    //     "timestamp": "2025-02-15T12:30:00Z",
    //     "found": false,
    //     "message": "No temperature/humidity data found for this timestamp"
    // }
    ```

7.  Nodes by energy cost (greater than or equal to):
    ```json
    {
        "request": "id_energy_cost", // Note: In the code, it's "id_energy_cost"
        "client_id": "client-1",
        "data": 15.75 // Minimum energy cost
    }
    ```
    Response on `rust/response/client-1/energy_cost`:
    ```json
    [ // Can be paginated!
        { "id": 101, "energy_cost": 16.0 /* ... */ },
        { "id": 102, "energy_cost": 20.5 /* ... */ }
    ]
    // For pagination: Similar to time_range.
    ```

8.  Nodes by energy consumption (greater than or equal to):
    ```json
    {
        "request": "id_energy_consume", // Note: In the code, it's "id_energy_consume"
        "client_id": "client-1",
        "data": 100.5 // Minimum energy consumption
    }
    ```
    Response on `rust/response/client-1/energy_consume`:
    ```json
    [ // Can be paginated!
        { "id": 201, "energy_consume": 110.0 /* ... */ }
    ]
    // For pagination: Similar to time_range.
    ```

9.  Get newest IDs:
    ```json
    {
        "request": "newestids",
        "client_id": "client-1"
    }
    ```
    Response on `rust/response/client-1/newestids`:
    ```json
    [ // Can be paginated!
        { "id": 999, "timestamp": "2025-05-16T10:00:00Z" /* ... */ },
        { "id": 998, "timestamp": "2025-05-16T09:59:00Z" /* ... */ }
    ]
    // For pagination: Similar to time_range.
    ```

10. Get newest sensor data:
    ```json
    {
        "request": "newestsensordata",
        "client_id": "client-1"
    }
    ```
    Response on `rust/response/client-1/newestsensordata`:
    ```json
    [ // Can be paginated!
        { "id": 801, "type": "SensorData", "temperature": 22.1, "humidity": 46.0 /* ... */ }
    ]
    // For pagination: Similar to time_range.
    ```

11. Get newest energy data:
    ```json
    {
        "request": "newestenergydata",
        "client_id": "client-1"
    }
    ```
    Response on `rust/response/client-1/newestenergydata`:
    ```json
    [ // Can be paginated!
        { "id": 701, "type": "EnergyData", "consumption": 5.5, "cost": 0.8 /* ... */ }
    ]
    // For pagination: Similar to time_range.
    ```

12. Add/Update robot data:
    ```json
    {
        "request": "addrobotdata",
        "client_id": "client-1",
        "data": { /* Structure of robot data, see implementation for details */ }
    }
    ```
    Response on `rust/response/client-1/add/robotdata`:
    ```json
    {
        "status": "success", // or "no_change"
        "message": "Successfully processed X nodes/relations", // or "No new nodes or relations..."
        "count": 1 // Number of created/updated elements
    }
    // Additionally, live data is published on `rust/response/livedata`:
    // {
    //     "type": "robotdata",
    //     "source": "mqtt",
    //     "client_id": "client-1",
    //     "timestamp": "...",
    //     "count": 1,
    //     "data": { /* the sent data */ }
    // }
    ```

13. Add/Update energy data:
    ```json
    {
        "request": "addenergydata",
        "client_id": "client-1",
        "data": { /* Structure of energy data */ }
    }
    ```
    Response on `rust/response/client-1/add/energydata`:
    ```json
    {
        "status": "success",
        "message": "Successfully processed X energy nodes",
        "count": 1
    }
    // Live data on `rust/response/livedata` (type: "energydata")
    ```

14. Add/Update sensor data:
    ```json
    {
        "request": "addsensordata",
        "client_id": "client-1",
        "data": { /* Structure of sensor data */ }
    }
    ```
    Response on `rust/response/client-1/add/sensordata`:
    ```json
    {
        "status": "success",
        "message": "Successfully processed X sensor nodes",
        "count": 1
    }
    // Live data on `rust/response/livedata` (type: "sensordata")
    ```

15. Export data with relationships:
    ```json
    {
        "request": "relation",
        "client_id": "client-1"
    }
    ```
    Response on `rust/response/client-1/relation`:
    **ATTENTION:** This response is very likely to be paginated!
    ```json
    // Example of a part of the response (can be very large)
    // Structure similar to "all", but with additional relationship data.
    // {
    //     "type": "paginated",
    //     "request_id": "relation-export-id",
    //     "page": 1,
    //     "total_pages": 10, // Example
    //     "data": [
    //         {
    //             "node": { "id": 1, "name": "Robot Alpha" /* ... */ },
    //             "relationships": [
    //                 { "type": "CONNECTED_TO", "direction": "outgoing", "target_node": { "id": 2, "name": "Sensor Beta" } }
    //             ]
    //         }
    //         // ...
    //     ]
    // }
    // Pagination like "all".
    ```

16. Get paginated IDs (page by page):
    ```json
    {
        "request": "page",
        "client_id": "client-1",
        "data": 1 // Page number (starting from 1)
    }
    ```
    Response on `rust/response/client-1/page`:
    ```json
    {
        // The response directly contains the data for the requested page.
        // The structure of the data depends on what `get_paginated_ids` returns.
        // Example:
        "page_number": 1,
        "items_per_page": 100, // Assumption
        "total_items": 1000, // Assumption
        "data": [
            { "id": 1 /* ... */ },
            { "id": 2 /* ... */ }
            // ... up to 100 items for this page
        ]
    }
    // This request is for specific pagination scenarios, and
    // the response itself is typically NOT paginated again by the MQTT publisher logic,
    // as it already represents a single page.
    ```

17. Delete data (by IDs):
    ```json
    {
        "request": "delete",
        "client_id": "client-1",
        "data": [123, 456, 789] // Array of numerical IDs to be deleted
    }
    ```
    Response on `rust/response/client-1/delete`:
    ```json
    {
        "status": "success", // or "not_found" if no IDs matched
        "message": "Successfully deleted 3 node(s).", // or "No nodes found matching the provided IDs."
        "deleted_count": 3
    }
    ```




