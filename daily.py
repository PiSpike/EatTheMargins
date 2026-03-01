import os
import json
from datetime import datetime, timedelta
import time
# Import your existing scripts/functions
from scrape_data import scrape_menu, update_database
from gemini import enrich_database_batched # Assume this is your Gemini function

def get_dining_date():
    """Returns the date string. If before 6 AM, returns yesterday."""
    now = datetime.now()
    if now.hour < 6:
        now = now - timedelta(days=1)
    return now.strftime('%Y-%m-%d')

def run_daily_update():
    date_str = get_dining_date()
    print(f"--- Starting Update for {date_str} ---")
    
    # 1. Scrape the CSV
    csv_path = f"sfu_menu.csv"
    scrape_menu(date_str) # Your function that saves the CSV
    
    # 2. Update the local JSON database and History
    # This adds new IDs to inventory.json and sets cost to None
    update_database(csv_path, date_str)
    
    # 3. Enrich with Gemini
    # We only send items where estimated_cost_cents is None
    print("Enriching new items with Gemini...")
    enrich_database_batched()
    enrich_database_batched()
    
    print(f"--- Update Complete for {date_str} ---")

if __name__ == "__main__":
    run_daily_update()