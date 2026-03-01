from google import genai
import json
import time
import os
from dotenv import load_dotenv
import random

# --- CONFIGURATION ---
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
INVENTORY_FILE = "inventory.json"
BATCH_SIZE = 20 

client = genai.Client(api_key=GEMINI_API_KEY)

def enrich_database_batched():
    if not os.path.exists(INVENTORY_FILE):
        print("Inventory file not found!")
        return

    with open(INVENTORY_FILE, 'r') as f:
        inventory = json.load(f)

    to_process_ids = [id for id, data in inventory.items() if data.get('estimated_cost_cents') is None]
    print(f"Total items to process: {len(to_process_ids)}")

    for i in range(0, len(to_process_ids), BATCH_SIZE):
        batch_ids = to_process_ids[i:i + BATCH_SIZE]
        batch_data = [{"id": b_id, "name": inventory[b_id]['name'], 
                       "ingredients": inventory[b_id]['ingredients']} for b_id in batch_ids]

        success = False
        retries = 0
        
        while not success and retries < 3:
            print(f"Processing batch {i//BATCH_SIZE + 1} (Attempt {retries + 1})...")
            
            prompt = f"""
            Context: You are a commercial kitchen auditor for a university buffet in BC, Canada.
            Task: Estimate the raw wholesale cost (COGS) in CAD cents for ONE portion of EACH item provided below.

            ITEMS TO AUDIT:
            {json.dumps(batch_data, indent=2)}

            Rules:
            1. Estimate based on 2026 wholesale bulk prices (e.g., 20kg bags, bulk cases).
            2. If ingredients are "No ingredients listed", infer from the Item Name.
            3. Account strictly for the "portion" provided (e.g., "1 each" vs "100g").
            4. I would rather you underestimate rather than overestimate
            5. Return ONLY a valid JSON array of objects.

            Required JSON Keys for each object:
            - "id": (The original ID provided)
            - "cost_cents": (Integer estimate)
            - "reasoning": (Brief explanation, e.g., "Bulk beef cost @ $14/kg for 150g portion")

            Example Output Format:
            [
            {{"id": "123", "cost_cents": 85, "reasoning": "Bulk chicken @ $11/kg for 120g portion"}},
            {{"id": "456", "cost_cents": 30, "reasoning": "Standard 250ml milk carton wholesale"}}
            ]

            JSON Response:
            """
            # prompt = f"""
            # Estimate wholesale cost (COGS) in CAD cents for one portion of each item.
            # ITEMS: {json.dumps(batch_data)}
            # Return ONLY a JSON array of objects with keys: "id", "cost_cents", "reasoning".
            # """

            try:
                response = client.models.generate_content(
                    model="gemma-3-12b-it", 
                    contents=prompt
                )
                
                raw_text = response.text.replace('```json', '').replace('```', '').strip()
                results = json.loads(raw_text)

                for res in results:
                    target_id = str(res['id'])
                    if target_id in inventory:
                        inventory[target_id]['estimated_cost_cents'] = res['cost_cents']
                        inventory[target_id]['cost_reasoning'] = res['reasoning']

                with open(INVENTORY_FILE, 'w', encoding='utf-8') as f:
                    json.dump(inventory, f, indent=2)
                
                print(f"DONE: Saved batch {i//BATCH_SIZE + 1}")
                success = True
                time.sleep(5) # 10s delay to be extra safe with the 15 RPM limit

            except Exception as e:
                retries += 1
                wait_time = (10 * retries) + random.random()
                print(f"API Error: {str(e)[:100]}") # Only print the first 100 chars to avoid terminal issues
                print(f"Waiting {wait_time:.1f}s before retry...")
                time.sleep(wait_time)

    print("Enrichment complete!")

if __name__ == "__main__":
    enrich_database_batched()