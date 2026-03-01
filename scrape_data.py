import requests
import csv
import json
import pandas as pd
from datetime import datetime, timedelta
import os

LOCATION_ID = "63fd054f92d6b41e84b6c30e"
#DATE = "2026-02-28"
HEADERS = {"User-Agent": "Mozilla/5.0"}

def get_dining_date():
    """Returns the date string. If before 6 AM, returns yesterday."""
    now = datetime.now()
    if now.hour < 6:
        now = now - timedelta(days=1)
    return now.strftime('%Y-%m-%d')


def scrape_menu(date_string):
    # This is the "Master Key" URL that finds the IDs for us
    discovery_url = f"https://api.dineoncampus.ca/v1/location/{LOCATION_ID}/periods?platform=0&date={date_string}"
    
    try:
        # Step 1: Find today's specific IDs
        periods_resp = requests.get(discovery_url, headers=HEADERS).json()
        active_periods = periods_resp.get('periods', [])
        
        if not active_periods:
            print(f"No periods found for {date_string}. Is the location closed?")
            return

    except Exception as e:
        print(f"Failed to discover periods: {e}")
        return

    with open('sfu_menu.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["ID", "Meal", "Category", "Item", "Portion", "Calories", "Protein", "Fat", "Carbs", "Sugar", "Ingredients"])

        for p in active_periods:
            meal_name = p.get('name')
            p_id = p.get('id')
            
            print(f"Fetching {meal_name} (ID: {p_id})...")
            url = f"https://api.dineoncampus.ca/v1/location/{LOCATION_ID}/periods/{p_id}?platform=0&date={date_string}"
            
            try:
                data = requests.get(url, headers=HEADERS).json()
                # Use a very safe way to get categories regardless of nesting
                menu = data.get('menu', {})
                periods_data = menu.get('periods', [])
                
                # Handle if periods_data is a list (like your links showed)
                if isinstance(periods_data, list) and len(periods_data) > 0:
                    categories = periods_data[0].get('categories', [])
                elif isinstance(periods_data, dict):
                    categories = periods_data.get('categories', [])
                else:
                    categories = []

                for cat in categories:
                    for item in cat.get('items', []):
                        # Create a quick map of nutrients
                        nuts = {n.get('name'): n.get('value') for n in item.get('nutrients', [])}

                        writer.writerow([
                            item.get('id'),
                            meal_name,
                            cat.get('name'),
                            item.get('name'),
                            item.get('portion', '1 serving'), # <--- EXTRACTING PORTION
                            nuts.get('Calories', '0'),
                            nuts.get('Protein (g)', '0'),
                            nuts.get('Total Fat (g)', '0'),
                            nuts.get('Total Carbohydrates (g)', '0'),
                            nuts.get('Sugar (g)', '0'),
                            item.get('ingredients', 'No ingredients listed')
                        ])
            except Exception as e:
                print(f"  Error scraping {meal_name}: {e}")

    print("Success! Check sfu_menu.csv")


def update_database(scrape_csv_path, date_string):
    inventory_path = 'inventory.json'
    history_path = 'menu_history.json'
    
    # 1. Load existing inventory (we want to keep this to save Gemini costs!)
    if os.path.exists(inventory_path):
        with open(inventory_path, 'r') as f:
            inventory = json.load(f)
    else:
        inventory = {}

    # 2. START FRESH for history (This is the change you wanted)
    # We do NOT load history from file. We start with an empty dict.
    history = {} 

    df = pd.read_csv(scrape_csv_path)
    
    # Initialize the date key in our fresh history object
    if date_string not in history:
        history[date_string] = {}

    for _, row in df.iterrows():
        item_id = str(row['ID'])
        meal_period = str(row['Meal']).upper()
        category_name = str(row['Category']).strip() if pd.notna(row['Category']) else 'General'

        # Update or Create Inventory Entry
        if item_id not in inventory:
            inventory[item_id] = {
                "name": row['Item'],
                "category": category_name, 
                "ingredients": row['Ingredients'] if pd.notna(row['Ingredients']) else "No ingredients listed",
                "nutrients": {
                    "protein": str(row['Protein']),
                    "fat": str(row['Fat']),
                    "carbs": str(row['Carbs']),
                    "calories": str(row['Calories'])
                },
                "portion": row['Portion'] if pd.notna(row['Portion']) else '1 serving',
                "estimated_cost_cents": None 
            }
        else:
            # Update the category/ingredients if they changed, but keep the cost!
            inventory[item_id]["category"] = category_name
        
        # Sync History (The "Daily Menu")
        if meal_period not in history[date_string]:
            history[date_string][meal_period] = []
        
        if item_id not in history[date_string][meal_period]:
            history[date_string][meal_period].append(item_id)

    # Save Inventory (Persistent data)
    with open(inventory_path, 'w') as f:
        json.dump(inventory, f, indent=2)

    # Save History (ONLY today's data)
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)

    print(f"Database synced. History cleared and updated for {date_string}.")

def export_json_to_csv(input_json='inventory.json', output_csv='master_inventory_export.csv'):
    if not os.path.exists(input_json):
        print(f"Error: {input_json} not found.")
        return

    # 1. Load the JSON data
    with open(input_json, 'r', encoding='utf-8') as f:
        inventory = json.load(f)

    # 2. Define the headers for our CSV
    headers = [
        "Item_ID", "Name", "Cost_Cents", "Cost_CAD", 
        "Calories", "Protein", "Fat", "Carbs", 
        "Portion", "Ingredients", "Cost_Reasoning"
    ]

    # 3. Write to CSV
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(headers)

        for item_id, data in inventory.items():
            # Get nutrients safely
            nuts = data.get('nutrients', {})
            
            # Calculate CAD price for readability (e.g., 150 cents -> $1.50)
            cents = data.get('estimated_cost_cents')
            cad_price = f"${cents/100:.2f}" if cents is not None else "N/A"

            writer.writerow([
                item_id,
                data.get('name', 'Unknown'),
                cents if cents is not None else "N/A",
                cad_price,
                nuts.get('calories', 0),
                nuts.get('protein', 0),
                nuts.get('fat', 0),
                nuts.get('carbs', 0),
                data.get('portion', '1 serving'),
                data.get('ingredients', ''),
                data.get('cost_reasoning', '')
            ])

    print(f"Success! Your database has been exported to: {output_csv}")

#scrape_menu(DATE)
#update_database('sfu_menu.csv', get_dining_date())
export_json_to_csv()
