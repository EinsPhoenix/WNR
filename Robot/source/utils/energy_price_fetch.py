import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
from utils.database_imp import DatabaseImp


class EnergyPriceFetcher:
    def __init__(self, parent, json_file_path="utils/energy_data.json"):
        self.parent = parent
        self.json_file_path = json_file_path
        self.api_url = "https://api.awattar.de/v1/marketdata"

    def get_timestamps(self):
        """Generate start (now) and end (48 hours later) timestamps in milliseconds."""
        now = datetime.now()
        end_time = now + timedelta(hours=48)
        start_timestamp = int(now.timestamp() * 1000)
        end_timestamp = int(end_time.timestamp() * 1000)
        return start_timestamp, end_timestamp

    def timestamp_to_datetime_string(self, timestamp_ms):
        """Convert timestamp in milliseconds to datetime string format."""
        dt = datetime.fromtimestamp(timestamp_ms / 1000)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    def process_api_data_for_database(self, api_data):
        """Process API response data for database insertion."""
        if not api_data or "data" not in api_data:
            return []
        processed_data = []
        for entry in api_data["data"]:
            processed_entry = {
                "timestamp": self.timestamp_to_datetime_string(
                    entry["start_timestamp"]
                ),
                "energy_cost": entry["marketprice"],
            }
            processed_data.append(processed_entry)
        return processed_data

    def should_fetch_data(self):
        """Check if data should be fetched based on last fetch time."""
        if not os.path.exists(self.json_file_path):
            return True
        try:
            with open(self.json_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            last_fetch = data.get("last_fetch_timestamp")
            if not last_fetch:
                return True

            last_fetch_time = datetime.fromtimestamp(last_fetch / 1000)
            current_time = datetime.now()
            time_diff = current_time - last_fetch_time
            if time_diff.total_seconds() > 24 * 3600:
                return True
            else:
                return False
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            return True

    async def fetch_energy_data(self):
        """Fetch energy data from the API."""
        start_timestamp, end_timestamp = self.get_timestamps()
        params = {"start": start_timestamp, "end": end_timestamp}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        result = {
                            "last_fetch_timestamp": int(
                                datetime.now().timestamp() * 1000
                            ),
                            "fetch_params": {
                                "start": start_timestamp,
                                "end": end_timestamp,
                            },
                            "api_response": data,
                        }
                        return result
                    else:
                        return None
        except Exception as e:
            return None

    def save_data(self, data):
        """Save data to JSON file."""
        try:
            with open(self.json_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            return False

    def load_data(self):
        """Load data from JSON file."""
        if not os.path.exists(self.json_file_path):
            return None
        try:
            with open(self.json_file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            return None

    async def send_to_database(self, processed_data):
        """Send processed energy data to database."""
        try:
            if await self.parent.db.connect():
                response = await self.parent.db.generate_energydata_struct(
                    processed_data
                )
                if response and response.get("status") == "success":
                    return True
        except Exception as e:

            return False
        return False

    async def run_daily_fetch(self):
        """Main method to run the daily fetch process."""
        if self.should_fetch_data():
            data = await self.fetch_energy_data()
            if data:
                if self.save_data(data):
                    processed_data = self.process_api_data_for_database(
                        data["api_response"]
                    )
                    if processed_data:
                        if await self.send_to_database(processed_data):
                            return True

                return False
            else:
                old_data = self.load_data()
                if old_data:
                    processed_data = self.process_api_data_for_database(
                        old_data.get("api_response")
                    )
                    if processed_data:
                        if await self.send_to_database(processed_data):
                            return True
                return False
        else:
            return True

    async def start_scheduler(self):
        """Start the scheduler that runs once per day."""
        while True:
            await self.run_daily_fetch()
            await asyncio.sleep(24 * 3600)
