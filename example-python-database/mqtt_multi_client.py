import paho.mqtt.client as mqtt
import json
import time
import uuid
import threading
import random
import re
import argparse
import os
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from typing import Dict, List, Any, Optional, Tuple

# Configuration
BROKER = "localhost"
PORT = 1883
USERNAME = "admin"
PASSWORD = "admin"
REQUEST_TOPIC = "rust/request"
RESPONSE_TOPIC_BASE = "rust/response/"


class MqttClient:
    def __init__(self, client_name=None):
        self.client_id = client_name or f"python-client-{str(uuid.uuid4())[:8]}"
        self.received_response = None
        self.response_received = threading.Event()
        self.start_time = None
        self.first_response_time = None
        self.end_time = None  # To track total response time

        self.paginated_messages = {}
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.username_pw_set(USERNAME, PASSWORD)
        self.lock = threading.Lock()

        # Performance metrics
        self.is_paginated = False
        self.total_pages_received = 0
        self.request_completed = False
        self.request_timed_out = False
        self.request_type = None
        self.request_failed = False

        self.setup_logging()

    def setup_logging(self):
        """Initialize logging for this client"""
        if not os.path.exists("logs"):
            os.makedirs("logs")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/log_client_{self.client_id}_{timestamp}.log"

        self.logger = logging.getLogger(self.client_id)
        self.logger.setLevel(logging.INFO)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)

        self.logger.info(f"Client {self.client_id} logging initialized")

    def on_connect(self, client, userdata, flags, rc):
        with self.lock:
            if rc == 0:
                log_msg = f"Client {self.client_id} connected to broker (Code: {rc})"
                print(f"✅ {log_msg}")
                self.logger.info(log_msg)
            else:
                log_msg = f"Client {self.client_id} connection error (Code: {rc})"
                print(f"❌ {log_msg}")
                self.logger.error(log_msg)

    def on_message(self, client, userdata, msg):
        try:
            if self.first_response_time is None:
                self.first_response_time = time.time()

            payload = json.loads(msg.payload.decode())

            # Check for paginated message format
            page_pattern = re.compile(r"(.*)/page/(\d+)")
            page_match = page_pattern.match(msg.topic)
            if page_match:
                with self.lock:
                    log_msg = f"Client {self.client_id} received paginated message part on {msg.topic}"
                    print(f"\n📄 {log_msg}")
                    self.logger.info(log_msg)
                self.handle_paginated_message(page_match, payload)
                self.is_paginated = True
                return

            # Check for pagination summary
            if msg.topic.endswith("/summary"):
                with self.lock:
                    log_msg = f"Client {self.client_id} received pagination summary on {msg.topic}"
                    print(f"\n📋 {log_msg}")
                    self.logger.info(log_msg)
                self.handle_pagination_summary(msg.topic, payload)
                self.is_paginated = True
                return

            # Handle new paginated format (for "page" requests)
            if (
                isinstance(payload, dict)
                and "total_pages" in payload
                and "page_content" in payload
            ):
                with self.lock:
                    log_msg = f"Client {self.client_id} received paginated response on {msg.topic}"
                    print(f"\n📋 {log_msg}")
                    self.logger.info(log_msg)
                self.handle_new_pagination_format(msg.topic, payload)
                self.is_paginated = True
                return

            # Regular response
            with self.lock:
                log_msg = f"Client {self.client_id} received response on {msg.topic}"
                print(f"\n📨 {log_msg}")
                self.logger.info(log_msg)

                payload_str = json.dumps(payload)
                self.logger.info(f"Payload preview: {payload_str[:200]}...")
                print(json.dumps(payload, indent=2))
            self.received_response = payload
            self.end_time = time.time()
            self.request_completed = True

            if (
                isinstance(self.received_response, dict)
                and self.received_response.get("status") == "error"
            ):
                self.request_failed = True
                with self.lock:
                    log_msg = f"Client {self.client_id} request marked as FAILED due to status: error"
                    print(f"❌ {log_msg}")
                    self.logger.warning(log_msg)
            self.response_received.set()

        except json.JSONDecodeError:
            with self.lock:
                log_msg = (
                    f"Client {self.client_id} received invalid JSON: {msg.payload}"
                )
                print(f"⚠️ {log_msg}")
                self.logger.error(log_msg)

    def handle_new_pagination_format(self, topic, payload):
        """Handle new pagination format from the 'page' request type"""
        total_pages = payload.get("total_pages", 0)
        current_page = payload.get("current_page", 1)
        page_content = payload.get("page_content", [])

        with self.lock:
            log_msg = f"Pagination data: Page {current_page} of {total_pages} with {len(page_content)} items"
            print(f"📊 {log_msg}")
            self.logger.info(log_msg)

        self.received_response = payload
        self.end_time = time.time()
        self.request_completed = True
        self.response_received.set()

    def handle_paginated_message(self, match, payload):
        base_topic = match.group(1)
        page_num = int(match.group(2))

        request_id = payload.get("request_id")
        if not request_id:
            with self.lock:
                log_msg = f"Paginated message missing request_id: {payload}"
                print(f"⚠️ {log_msg}")
                self.logger.warning(log_msg)
            return

        message_id = f"{base_topic}_{request_id}"

        if message_id not in self.paginated_messages:
            self.paginated_messages[message_id] = {
                "total_pages": payload.get("total_pages", 0),
                "pages": {},
                "received_pages": 0,
                "complete": False,
            }

        if self.paginated_messages[message_id]["total_pages"] == 0:
            self.paginated_messages[message_id]["total_pages"] = payload.get(
                "total_pages", 0
            )

        self.paginated_messages[message_id]["pages"][page_num] = payload.get("data", [])
        self.paginated_messages[message_id]["received_pages"] += 1
        self.total_pages_received += 1

        with self.lock:
            log_msg = f"Received page {page_num}/{self.paginated_messages[message_id]['total_pages']} for {message_id}"
            print(f"📄 {log_msg}")
            self.logger.info(log_msg)

        if (
            self.paginated_messages[message_id]["received_pages"]
            == self.paginated_messages[message_id]["total_pages"]
        ):
            with self.lock:
                log_msg = f"All pages received for {message_id}, reassembling..."
                print(f"🔄 {log_msg}")
                self.logger.info(log_msg)
            self.reassemble_paginated_message(message_id)

    def handle_pagination_summary(self, topic, payload):
        request_id = payload.get("request_id")
        total_pages = payload.get("total_pages", 0)
        base_topic = payload.get("topic_base")

        if not request_id or not base_topic:
            with self.lock:
                log_msg = f"Summary message missing critical data: {payload}"
                print(f"⚠️ {log_msg}")
                self.logger.warning(log_msg)
            return

        message_id = f"{base_topic}_{request_id}"

        with self.lock:
            log_msg = f"Summary for {message_id}: {total_pages} pages, {payload.get('total_items', 0)} items"
            print(f"📋 {log_msg}")
            self.logger.info(log_msg)

        if (
            message_id in self.paginated_messages
            and self.paginated_messages[message_id]["received_pages"] == total_pages
        ):
            with self.lock:
                log_msg = (
                    f"All pages already received for {message_id}, reassembling..."
                )
                print(f"🔄 {log_msg}")
                self.logger.info(log_msg)
            self.reassemble_paginated_message(message_id)

    def reassemble_paginated_message(self, message_id):
        if not self.paginated_messages[message_id]["complete"]:
            data = self.paginated_messages[message_id]

            all_items = []
            for page_num in sorted(data["pages"].keys()):
                all_items.extend(data["pages"][page_num])

            with self.lock:
                log_msg = f"Reassembled {len(all_items)} items from {len(data['pages'])} pages"
                print(f"✅ {log_msg}")
                self.logger.info(log_msg)

            self.paginated_messages[message_id]["complete"] = True

            self.received_response = all_items
            self.end_time = time.time()
            self.request_completed = True

            if (
                isinstance(self.received_response, dict)
                and self.received_response.get("status") == "error"
            ):
                self.request_failed = True
                with self.lock:
                    log_msg = f"Client {self.client_id} paginated request marked as FAILED due to status: error"
                    print(f"❌ {log_msg}")
                    self.logger.warning(log_msg)

            elif (
                isinstance(all_items, list)
                and all_items
                and isinstance(all_items[0], dict)
                and all_items[0].get("status") == "error"
            ):
                self.request_failed = True
                with self.lock:
                    log_msg = f"Client {self.client_id} paginated request marked as FAILED due to status: error in first item"
                    print(f"❌ {log_msg}")
                    self.logger.warning(log_msg)

            self.response_received.set()

            filename = f"paginated_response_{self.client_id}_{int(time.time())}.json"
            with open(filename, "w") as f:
                json.dump(all_items, f, indent=2)

            with self.lock:
                log_msg = f"Paginated response saved to {filename}"
                print(f"💾 {log_msg}")
                self.logger.info(log_msg)

    def send_request(self, query_data, response_suffix, timeout=15):
        self.response_received.clear()
        self.received_response = None
        self.paginated_messages = {}
        self.first_response_time = None
        self.end_time = None
        self.is_paginated = False
        self.total_pages_received = 0
        self.request_completed = False
        self.request_timed_out = False
        self.request_type = response_suffix
        self.request_failed = False

        try:
            self.client.connect(BROKER, PORT)
            self.client.loop_start()

            if "request" in query_data and query_data["request"] == "uuid":
                response_topic = f"rust/uuid/{self.client_id}"
            else:
                response_topic = (
                    f"{RESPONSE_TOPIC_BASE}{self.client_id}/{response_suffix}"
                )

            page_wildcard = f"{response_topic}/page/#"
            summary_topic = f"{response_topic}/summary"

            self.client.subscribe(response_topic)
            self.client.subscribe(page_wildcard)
            self.client.subscribe(summary_topic)

            with self.lock:
                self.logger.info(f"Subscribed to: {response_topic}")
                self.logger.info(f"Subscribed to: {page_wildcard}")
                self.logger.info(f"Subscribed to: {summary_topic}")
                print(f"🔔 Client {self.client_id} subscribed to: {response_topic}")
                print(f"🔔 Client {self.client_id} subscribed to: {page_wildcard}")
                print(f"🔔 Client {self.client_id} subscribed to: {summary_topic}")

            query_data["client_id"] = self.client_id

            self.start_time = time.time()
            self.client.publish(REQUEST_TOPIC, json.dumps(query_data))

            with self.lock:
                log_msg = (
                    f"Client {self.client_id} sent request: {json.dumps(query_data)}"
                )
                print(f"📤 {log_msg}")
                self.logger.info(log_msg)

            timeout = 30 if "all" in response_suffix else timeout
            result = self.response_received.wait(timeout)

            elapsed_time = None
            if self.first_response_time is not None:
                elapsed_time = self.first_response_time - self.start_time

            with self.lock:
                if elapsed_time is not None:
                    log_msg = f"Client {self.client_id} first response received in {elapsed_time:.3f} seconds"
                    print(f"⏱️ {log_msg}")
                    self.logger.info(log_msg)
                else:
                    log_msg = f"Client {self.client_id} did not receive any response"
                    print(f"⏱️ {log_msg}")
                    self.logger.warning(log_msg)

                if result:
                    log_msg = f"Client {self.client_id} received complete response"
                    print(f"✅ {log_msg}")
                    self.logger.info(log_msg)
                else:
                    log_msg = (
                        f"Client {self.client_id} timed out after {timeout} seconds"
                    )
                    print(f"⌛ {log_msg}")
                    self.logger.warning(log_msg)
                    self.request_timed_out = True

            return self.received_response

        finally:
            self.client.loop_stop()
            self.client.disconnect()

    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this client"""
        metrics = {
            "client_id": self.client_id,
            "request_type": self.request_type,
            "start_time": self.start_time,
            "first_response_time": self.first_response_time,
            "end_time": self.end_time,
            "is_paginated": self.is_paginated,
            "total_pages": self.total_pages_received,
            "completed": self.request_completed,
            "timed_out": self.request_timed_out,
            "failed": self.request_failed,
        }

        if self.first_response_time and self.start_time:
            metrics["first_response_latency"] = (
                self.first_response_time - self.start_time
            )

        if self.end_time and self.start_time:
            metrics["total_duration"] = self.end_time - self.start_time

        return metrics


def run_test_client(client_name, request_type, params):
    """Run a single test client with the given parameters"""
    client = MqttClient(client_name)

    request_handlers = {
        "uuid": lambda: client.send_request(
            {"request": "uuid", "payload": [{"uuid": params.get("uuid", 1)}]}, "uuid"
        ),
        "all": lambda: client.send_request({"request": "all"}, "all"),
        "color": lambda: client.send_request(
            {"request": "color", "data": params.get("color", "red")}, "color"
        ),
        "time_range": lambda: client.send_request(
            {
                "request": "time_range",
                "start": params.get("start", "2025-01-01T00:00:00Z"),
                "end": params.get("end", "2025-03-01T00:00:00Z"),
            },
            "time_range",
        ),
        "temperature_humidity": lambda: client.send_request(
            {
                "request": "temperature_humidity",
                "temperature": params.get("temperature", 22.5),
                "humidity": params.get("humidity", 45.0),
            },
            "temperature_humidity",
        ),
        "timestamp": lambda: client.send_request(
            {
                "request": "timestamp",
                "data": params.get("timestamp", "2025-02-15T12:30:00Z"),
            },
            "timestamp",
        ),
        "energy_cost": lambda: client.send_request(
            {"request": "id_energy_cost", "data": params.get("cost", 0.25)},
            "energy_cost",
        ),
        "energy_consume": lambda: client.send_request(
            {"request": "id_energy_consume", "data": params.get("consume", 150.0)},
            "energy_consume",
        ),
        "newest": lambda: client.send_request({"request": "newestids"}, "newestids"),
        "newest_sensor": lambda: client.send_request(
            {"request": "newestsensordata"}, "newestsensordata"
        ),
        "newest_energy": lambda: client.send_request(
            {"request": "newestenergydata"}, "newestenergydata"
        ),
        "relation": lambda: client.send_request({"request": "relation"}, "relation"),
        "page": lambda: client.send_request(
            {"request": "page", "data": params.get("page", 1)}, "page"
        ),
        "add_robot": lambda: client.send_request(
            {"request": "addrobotdata", "data": params.get("data", [])}, "add/robotdata"
        ),
        "add_sensor": lambda: client.send_request(
            {"request": "addsensordata", "data": params.get("data", [])},
            "add/sensordata",
        ),
        "add_energy": lambda: client.send_request(
            {"request": "addenergydata", "data": params.get("data", [])},
            "add/energydata",
        ),
        "delete": lambda: client.send_request(
            {"request": "delete", "data": params.get("ids", [])}, "delete"
        ),
    }

    # Execute the appropriate handler
    if request_type in request_handlers:
        return request_handlers[request_type]()

    return None


def run_test_client_with_metrics(
    client_name, request_type, params
) -> Tuple[Optional[Any], Dict[str, Any]]:
    """Run a test client and return both result and metrics"""
    client = MqttClient(client_name)

    request_handlers = {
        "uuid": lambda: client.send_request(
            {"request": "uuid", "payload": [{"uuid": params.get("uuid", 1)}]}, "uuid"
        ),
        "all": lambda: client.send_request({"request": "all"}, "all"),
        "color": lambda: client.send_request(
            {"request": "color", "data": params.get("color", "red")}, "color"
        ),
        "time_range": lambda: client.send_request(
            {
                "request": "time_range",
                "start": params.get("start", "2025-01-01T00:00:00Z"),
                "end": params.get("end", "2025-03-01T00:00:00Z"),
            },
            "time_range",
        ),
        "temperature_humidity": lambda: client.send_request(
            {
                "request": "temperature_humidity",
                "temperature": params.get("temperature", 22.5),
                "humidity": params.get("humidity", 45.0),
            },
            "temperature_humidity",
        ),
        "timestamp": lambda: client.send_request(
            {
                "request": "timestamp",
                "data": params.get("timestamp", "2025-02-15T12:30:00Z"),
            },
            "timestamp",
        ),
        "energy_cost": lambda: client.send_request(
            {"request": "id_energy_cost", "data": params.get("cost", 0.25)},
            "energy_cost",
        ),
        "energy_consume": lambda: client.send_request(
            {"request": "id_energy_consume", "data": params.get("consume", 150.0)},
            "energy_consume",
        ),
        "newest": lambda: client.send_request({"request": "newestids"}, "newestids"),
        "newest_sensor": lambda: client.send_request(
            {"request": "newestsensordata"}, "newestsensordata"
        ),
        "newest_energy": lambda: client.send_request(
            {"request": "newestenergydata"}, "newestenergydata"
        ),
        "relation": lambda: client.send_request({"request": "relation"}, "relation"),
        "page": lambda: client.send_request(
            {"request": "page", "data": params.get("page", 1)}, "page"
        ),
        "add_robot": lambda: client.send_request(
            {"request": "addrobotdata", "data": params.get("data", [])}, "add/robotdata"
        ),
        "add_sensor": lambda: client.send_request(
            {"request": "addsensordata", "data": params.get("data", [])},
            "add/sensordata",
        ),
        "add_energy": lambda: client.send_request(
            {"request": "addenergydata", "data": params.get("data", [])},
            "add/energydata",
        ),
        "delete": lambda: client.send_request(
            {"request": "delete", "data": params.get("ids", [])}, "delete"
        ),
    }

    # Execute the appropriate handler
    if request_type in request_handlers:
        result = request_handlers[request_type]()
        return result, client.get_metrics()

    client.logger.error(f"Unknown request type: {request_type}")
    return None, client.get_metrics()


def run_multiple_clients(num_clients=5, test_type=None):
    """Run multiple clients simultaneously"""
    test_types = [
        "uuid",
        "all",
        "color",
        "time_range",
        "temperature_humidity",
        "timestamp",
        "energy_cost",
        "energy_consume",
        "newest",
        "newest_sensor",
        "newest_energy",
        "relation",
        "page",
    ]

    if test_type and test_type not in test_types:
        print(f"Invalid test type: {test_type}")
        return

    tasks = []
    all_metrics = []

    for i in range(num_clients):
        client_name = f"test-client-{i+1}"

        selected_test = test_type or random.choice(test_types)

        # Prepare parameters with slight variations
        params = {}
        if selected_test == "uuid":
            params["uuid"] = i + 1
        elif selected_test == "color":
            colors = ["red", "green", "blue", "yellow", "purple"]
            params["color"] = colors[i % len(colors)]
        elif selected_test == "time_range":
            params["start"] = f"2025-0{(i % 12)+1}-01T00:00:00Z"
            params["end"] = f"2025-0{((i+1) % 12)+1}-01T00:00:00Z"
        elif selected_test == "temperature_humidity":
            params["temperature"] = 20.0 + i
            params["humidity"] = 40.0 + i
        elif selected_test == "timestamp":
            params["timestamp"] = f"2025-02-{(15+i) % 28}T12:30:00Z"
        elif selected_test == "energy_cost":
            params["cost"] = 0.20 + (i * 0.05)
        elif selected_test == "energy_consume":
            params["consume"] = 100.0 + (i * 50.0)
        elif selected_test == "page":
            params["page"] = (i % 5) + 1  # Pages 1-5

        tasks.append((client_name, selected_test, params))

    print(f"🚀 Starting {num_clients} clients simultaneously...")

    with ThreadPoolExecutor(max_workers=num_clients) as executor:
        futures = [
            executor.submit(run_test_client_with_metrics, name, test, params)
            for name, test, params in tasks
        ]

        for future in futures:
            _, metrics = future.result()
            all_metrics.append(metrics)

    print(f"✅ All client tests completed")

    generate_benchmark_report(all_metrics)


def generate_benchmark_report(metrics):
    """Generate a report of performance metrics from the test run"""
    if not metrics:
        print("No metrics available to generate report.")
        return

    if not os.path.exists("logs"):
        os.makedirs("logs")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"logs/benchmark_report_{timestamp}.txt"

    total_clients = len(metrics)
    completed_requests = sum(1 for m in metrics if m.get("completed", False))
    timed_out_requests = sum(1 for m in metrics if m.get("timed_out", False))
    failed_requests = sum(1 for m in metrics if m.get("failed", False))
    paginated_requests = sum(1 for m in metrics if m.get("is_paginated", False))
    non_paginated_requests = total_clients - paginated_requests

    response_times = [
        m.get("first_response_latency")
        for m in metrics
        if m.get("first_response_latency") is not None
    ]
    avg_response_time = (
        sum(response_times) / len(response_times) if response_times else 0
    )

    total_durations = [
        m.get("total_duration") for m in metrics if m.get("total_duration") is not None
    ]
    avg_total_duration = (
        sum(total_durations) / len(total_durations) if total_durations else 0
    )

    request_types = {}
    for m in metrics:
        req_type = m.get("request_type")
        if req_type:
            if req_type not in request_types:
                request_types[req_type] = {
                    "count": 0,
                    "completed": 0,
                    "timed_out": 0,
                    "failed": 0,
                    "response_times": [],
                }

            request_types[req_type]["count"] += 1

            if m.get("completed", False):
                request_types[req_type]["completed"] += 1

            if m.get("timed_out", False):
                request_types[req_type]["timed_out"] += 1

            if m.get("failed", False):
                request_types[req_type]["failed"] += 1

            if m.get("first_response_latency") is not None:
                request_types[req_type]["response_times"].append(
                    m.get("first_response_latency")
                )

    # Generate report
    with open(report_file, "w") as f:
        f.write(f"MQTT CLIENT BENCHMARK REPORT - {timestamp}\n")
        f.write("=" * 60 + "\n\n")

        f.write("SUMMARY\n")
        f.write("-" * 30 + "\n")
        f.write(f"Total Clients: {total_clients}\n")
        f.write(f"Completed Requests: {completed_requests}\n")
        f.write(f"Timed Out Requests: {timed_out_requests}\n")
        f.write(f"Failed Requests: {failed_requests}\n")
        f.write(f"Average Response Time: {avg_response_time:.3f} seconds\n")
        f.write(f"Average Total Duration: {avg_total_duration:.3f} seconds\n")
        f.write(f"Paginated Responses: {paginated_requests}\n")
        f.write(f"Non-paginated Responses: {non_paginated_requests}\n\n")

        f.write("REQUEST TYPE BREAKDOWN\n")
        f.write("-" * 30 + "\n")
        for req_type, data in request_types.items():
            avg_time = (
                sum(data["response_times"]) / len(data["response_times"])
                if data["response_times"]
                else 0
            )
            f.write(f"Type: {req_type}\n")
            f.write(f"  Count: {data['count']}\n")
            f.write(f"  Completed: {data['completed']}\n")
            f.write(f"  Timed Out: {data['timed_out']}\n")
            f.write(f"  Failed: {data['failed']}\n")
            f.write(f"  Average Response Time: {avg_time:.3f} seconds\n\n")

    print("\n📊 BENCHMARK REPORT SUMMARY")
    print("-" * 30)
    print(f"Total Clients: {total_clients}")
    print(f"Completed Requests: {completed_requests}")
    print(f"Timed Out Requests: {timed_out_requests}")
    print(f"Failed Requests: {failed_requests}")
    print(f"Average Response Time: {avg_response_time:.3f} seconds")
    print(f"Paginated Responses: {paginated_requests}")
    print(f"Non-paginated Responses: {non_paginated_requests}")
    print(f"Full report saved to: {report_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="MQTT Multi-Client Test Tool")
    parser.add_argument(
        "--clients",
        type=int,
        default=5,
        help="Number of simultaneous clients (5-20 recommended)",
    )
    parser.add_argument(
        "--test",
        type=str,
        choices=[
            "uuid",
            "all",
            "color",
            "time_range",
            "temperature_humidity",
            "timestamp",
            "energy_cost",
            "energy_consume",
            "newest",
            "newest_sensor",
            "newest_energy",
            "relation",
            "page",
            "add_robot",
            "add_sensor",
            "add_energy",
            "delete",
        ],
        help="Specific test to run (if not specified, random tests will be chosen)",
    )

    args = parser.parse_args()

    if args.clients < 1:
        args.clients = 1
    elif args.clients > 50:
        print("Warning: Limiting to 50 clients to prevent overloading")
        args.clients = 50

    run_multiple_clients(args.clients, args.test)
