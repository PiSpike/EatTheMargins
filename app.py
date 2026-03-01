from flask import Flask, render_template
import json
from datetime import datetime

app = Flask(__name__)

def get_todays_menu():
    # Load your files
    with open('inventory.json', 'r') as f:
        inventory = json.load(f)
    with open('menu_history.json', 'r') as f:
        history = json.load(f)

    today = datetime.now().strftime('%Y-%m-%d')
    # history[today] might look like {"LUNCH": ["id1", "id2"], "DINNER": [...]}
    
    day_data = history.get(today, {})
    all_items = []

    for period, ids in day_data.items():
        for iid in ids:
            item = inventory.get(iid)
            if item:
                item['period'] = period
                # Ensure there's a cost; default to 0 if Gemma hasn't tagged it yet
                item['cost'] = item.get('estimated_cost_cents', 0) / 100 
                all_items.append(item)

    # Sort by cost descending
    sorted_items = sorted(all_items, key=lambda x: x['cost'], reverse=True)
    return sorted_items

@app.route('/')
def home():
    menu = get_todays_menu()
    top_item = menu[0] if menu else None
    rest_of_menu = menu[1:] if len(menu) > 1 else []
    
    return render_template('index.html', top_item=top_item, menu=rest_of_menu)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)