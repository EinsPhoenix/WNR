# MQTT Client Test Tool - Documentation

## 📌 Overview

This tool provides a comprehensive MQTT client implementation for testing and benchmarking MQTT brokers with various request types. It supports single client operations, concurrent client testing, and detailed performance metrics collection.

## ✨ Features

- **Multiple Request Types**: 11 different request types supported
- **Concurrent Testing**: Run multiple clients simultaneously
- **Performance Metrics**: Detailed timing and success metrics
- **Pagination Support**: Automatic handling of paginated responses
- **Logging**: Comprehensive logging for debugging and analysis
- **Benchmark Reports**: Automated report generation

## 🚀 Quick Start

1. **Install dependencies**:
   ```bash
   pip install paho-mqtt
   ```

2. **Run a single test client**:
   ```bash
   python mqtt_client.py --clients 1 --test uuid
   ```

3. **Run concurrent clients**:
   ```bash
   python mqtt_client.py --clients 10 --test all
   ```

## 🔧 Configuration

Default configuration (can be modified in the code):

| Parameter       | Default Value  | Description                          |
|-----------------|----------------|--------------------------------------|
| `BROKER`        | `localhost`    | MQTT broker address                  |
| `PORT`          | `1883`         | MQTT broker port                     |
| `USERNAME`      | `admin`        | MQTT username                        |
| `PASSWORD`      | `admin`        | MQTT password                        |
| `REQUEST_TOPIC` | `rust/request` | Topic for sending requests           |
| `RESPONSE_TOPIC_BASE` | `rust/response/` | Base topic for receiving responses |

## 📋 Available Request Types

| Request Type            | Description                                                                 | Example Parameters                          |
|-------------------------|-----------------------------------------------------------------------------|---------------------------------------------|
| `uuid`                  | Request with UUID identifier                                                | `{"uuid": "abc123xyz001"}`                  |
| `all`                   | Request all available data (typically paginated)                            | None                                        |
| `color`                 | Request filtered by color                                                   | `{"color": "red"}`                          |
| `time_range`            | Request data within a specific time range                                   | `{"start": "2025-01-01", "end": "2025-03-01"}` |
| `temperature_humidity`  | Request with temperature and humidity parameters                            | `{"temperature": 22.5, "humidity": 45.0}`  |
| `timestamp`             | Request filtered by specific timestamp                                      | `{"timestamp": "2025-02-15T12:30:00Z"}`    |
| `energy_cost`           | Request with energy cost parameter                                          | `{"cost": 0.25}`                           |
| `energy_consume`        | Request with energy consumption parameter                                   | `{"consume": 150.0}`                       |
| `newest`                | Request the newest available data                                           | None                                        |
| `relation`              | Request data with relations                                                 | None                                        |
| `page`                  | Request specific page of data                                               | `{"page": 1}`                              |

## 📊 Performance Metrics

The tool collects the following metrics for each request:

| Metric                   | Description                                                                 |
|--------------------------|-----------------------------------------------------------------------------|
| `client_id`              | Unique identifier for the client                                           |
| `request_type`           | Type of request made                                                       |
| `start_time`             | When the request was initiated                                             |
| `first_response_time`    | When the first response was received                                       |
| `end_time`               | When the final response was received                                       |
| `is_paginated`           | Whether the response was paginated                                         |
| `total_pages`            | Number of pages received (if paginated)                                    |
| `completed`              | Whether the request completed successfully                                 |
| `timed_out`              | Whether the request timed out                                              |
| `first_response_latency` | Time from request to first response (seconds)                              |
| `total_duration`         | Total time from request to completion (seconds)                            |

## 📂 Logging Structure

All logs are stored in the `logs/` directory with the following naming convention:

```
logs/
├── log_client_[client_id]_[timestamp].log
└── benchmark_report_[timestamp].txt
```

## 🛠️ Command Line Arguments

| Argument      | Description                                                                 | Default | Options                                                                 |
|---------------|-----------------------------------------------------------------------------|---------|-------------------------------------------------------------------------|
| `--clients`   | Number of simultaneous clients to run                                       | 5       | 1-50 (recommended 5-20)                                                |
| `--test`      | Specific test type to run (if not specified, random tests will be chosen)   | None    | `uuid`, `all`, `color`, `time_range`, `temperature_humidity`, `timestamp`, `energy_cost`, `energy_consume`, `newest`, `relation`, `page` |

## 📈 Benchmark Report Example

```
MQTT CLIENT BENCHMARK REPORT - 20250101_123456
============================================================

SUMMARY
------------------------------
Total Clients: 10
Completed Requests: 8
Timed Out Requests: 2
Average Response Time: 1.243 seconds
Average Total Duration: 3.456 seconds
Paginated Responses: 3
Non-paginated Responses: 7

REQUEST TYPE BREAKDOWN
------------------------------
Type: uuid
  Count: 2
  Completed: 2
  Timed Out: 0
  Average Response Time: 0.456 seconds

Type: all
  Count: 1
  Completed: 1
  Timed Out: 0
  Average Response Time: 2.123 seconds
...
```

## 💡 Usage Examples

1. **Single client with UUID request**:
   ```bash
   python mqtt_client.py --clients 1 --test uuid
   ```

2. **5 clients with random request types**:
   ```bash
   python mqtt_client.py --clients 5
   ```

3. **10 clients requesting time range data**:
   ```bash
   python mqtt_client.py --clients 10 --test time_range
   ```

4. **Stress test with 20 clients**:
   ```bash
   python mqtt_client.py --clients 20 --test all
   ```

## ⚠️ Important Notes

1. The broker must be running and accessible at the configured address/port
2. For large numbers of clients (>20), monitor system resources
3. Paginated requests (`all`) typically take longer to complete
4. Timeout for paginated requests is automatically extended to 30 seconds

## 📜 License

This tool is provided as-is under the MIT License.