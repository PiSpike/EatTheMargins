from flask import Flask, render_template, request
import json
import os
from datetime import datetime

app = Flask(__name__)

def load_data():
    # Use absolute paths to avoid issues on the server
    base_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base_dir, 'inventory.json'), 'r') as f:
        inventory = json.load(f)
    with open(os.path.join(base_dir, 'menu_history.json'), 'r') as f:
        history = json.load(f)
    return inventory, history

@app.route('/')
def home():
    try:
        inventory, history = load_data()
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Determine the current meal period based on hour
        hour = datetime.now().hour
        if 6 <= hour < 10:
            current_period = "BREAKFAST"
        elif 10 <= hour < 17:
            current_period = "LUNCH"
        elif 17 <= hour < 22:
            current_period = "DINNER"
        else:
            current_period = "DAILY"

            
        return render_template('index.html', 
                               inventory_json=json.dumps(inventory), 
                               history_json=json.dumps(history),
                               today=today,
                               current_period=current_period)
    except Exception as e:
        return f"<h1>Error</h1><p>{str(e)}</p>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)