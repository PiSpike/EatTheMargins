#!/bin/bash
# 1. Navigate to the project directory
cd /root/eatthemargins

# 2. Run the scraper to generate the new CSV
/usr/bin/python3 daily.py

# 3. Check if master_inventory_export.csv has actually changed
# --porcelain returns an empty string if there are no changes
if [[ -n $(git status --porcelain master_inventory_export.csv) ]]; then
    echo "Changes detected in master_inventory_export.csv. Updating GitHub..."
    
    # Add, commit, and push only if changes exist
    git add master_inventory_export.csv menu_history.json inventory.json
    git commit -m "Auto-update menu: $(date +'%Y-%m-%d %H:%M')"
    git push origin main
else
    echo "No new data found in master_inventory_export.csv. Skipping push."
fi