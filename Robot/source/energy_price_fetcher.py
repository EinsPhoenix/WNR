import asyncio
import aiohttp
import json
import os
from datetime import datetime, timedelta
import time
from database_imp import Database_Imp

class EnergyPriceFetcher:
    def __init__(self, json_file_path="energy_data.json"):
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
        if not api_data or 'data' not in api_data:
            return []
        
        processed_data = []
        for entry in api_data['data']:
            processed_entry = {
                "timestamp": self.timestamp_to_datetime_string(entry['start_timestamp']),
                "energy_cost": entry['marketprice']
            }
            processed_data.append(processed_entry)
        
        return processed_data
    
    def should_fetch_data(self):
        """Check if data should be fetched based on last fetch time."""
        if not os.path.exists(self.json_file_path):
            print("No existing data file found. Will fetch new data.")
            return True
        
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            last_fetch = data.get('last_fetch_timestamp')
            if not last_fetch:
                print("No last fetch timestamp found. Will fetch new data.")
                return True
            
            # Convert to seconds for comparison
            last_fetch_time = datetime.fromtimestamp(last_fetch / 1000)
            current_time = datetime.now()
            time_diff = current_time - last_fetch_time
            
            if time_diff.total_seconds() > 24 * 3600:  # 24 hours in seconds
                print(f"Last fetch was {time_diff} ago. Will fetch new data.")
                return True
            else:
                print(f"Last fetch was {time_diff} ago. No need to fetch new data.")
                return False
                
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"Error reading existing data file: {e}. Will fetch new data.")
            return True
    
    async def fetch_energy_data(self):
        """Fetch energy data from the API."""
        start_timestamp, end_timestamp = self.get_timestamps()
        
        params = {
            'start': start_timestamp,
            'end': end_timestamp
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Add metadata
                        result = {
                            'last_fetch_timestamp': int(datetime.now().timestamp() * 1000),
                            'fetch_params': {
                                'start': start_timestamp,
                                'end': end_timestamp
                            },
                            'api_response': data
                        }
                        
                        return result
                    else:
                        print(f"API request failed with status {response.status}")
                        return None
                        
        except Exception as e:
            print(f"Error fetching data from API: {e}")
            return None
    
    def save_data(self, data):
        """Save data to JSON file."""
        try:
            with open(self.json_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Data saved to {self.json_file_path}")
            return True
        except Exception as e:
            print(f"Error saving data to file: {e}")
            return False
    
    def load_data(self):
        """Load data from JSON file."""
        if not os.path.exists(self.json_file_path):
            return None
        
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading data from file: {e}")
            return None
    
    async def send_to_database(self, processed_data):
        """Send processed energy data to database."""
        db = Database_Imp()
        
        try:
            if await db.connect():
                print(f"Sending {len(processed_data)} energy data entries to database...")
                response = await db.generate_energydata_struct(processed_data)
                
                if response and response.get('status') == 'success':
                    print("Energy data successfully sent to database.")
                    return True
                else:
                    print("Failed to send energy data to database.")
                    return False
            else:
                print("Failed to connect to database.")
                return False
        except Exception as e:
            print(f"Error sending data to database: {e}")
            return False
        finally:
            await db.disconnect()
    
    async def run_daily_fetch(self):
        """Main method to run the daily fetch process."""
        print(f"Starting energy price fetch process at {datetime.now()}")
        
        if self.should_fetch_data():
            print("Fetching new energy data...")
            data = await self.fetch_energy_data()
            
            if data:
                if self.save_data(data):
                    print("Energy data successfully fetched and saved.")
                    
                    processed_data = self.process_api_data_for_database(data['api_response'])
                    
                    if processed_data:
                        print(f"Processed {len(processed_data)} energy price entries.")

                        db_success = await self.send_to_database(processed_data)
                        
                        if db_success:
                            return True
                        else:
                            print("Warning: Data saved to file but failed to send to database.")
                            return True  
                    else:
                        print("No valid energy data to process.")
                        return False
                else:
                    print("Failed to save energy data.")
                    return False
            else:
                print("Failed to fetch energy data.")
                return False
        else:
            print("Skipping fetch - recent data already available.")
            return True
    
    async def start_scheduler(self):
        """Start the scheduler that runs once per day."""
        while True:
            await self.run_daily_fetch()
            
          
            print("Waiting 24 hours until next fetch...")
            await asyncio.sleep(24 * 3600)  


async def main():
    fetcher = EnergyPriceFetcher()
    
    # Run once immediately
    await fetcher.run_daily_fetch()
    
    # Uncomment the following line to start the scheduler
    # await fetcher.start_scheduler()

if __name__ == "__main__":
    asyncio.run(main())