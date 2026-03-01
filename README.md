# 🥗 Eat The Margins
**The SFU Dining Hall Value & Nutrition Tracker.**

Eat The Margins is a web application designed for students at Simon Fraser University to maximize the value of their meal plan. By scraping daily menu data and applying wholesale cost estimations, it identifies which meals provide the best "ROI" (Return on Investment) in terms of cost and nutrition.



## 🚀 Live Project
🔗 **[spikenet.net](https://spikenet.net)**

## ✨ Features
* **Value Calculation:** Real-time estimation of wholesale ingredient costs for every menu item.
* **Smart Filtering:** Toggle between Breakfast, Lunch, Dinner, and Daily staples.
* **The "Hero" Highlight:** Automatically promotes the "Most Valuable Item" currently available.
* **Protein+ Badge:** Identifies high-protein meals using a strict formula ($\ge 10\%$ protein-to-calorie ratio and $\ge 5g$ total protein).
* **Automated Scraper:** A Python-based cron job updates the menu database every morning at 6:05 AM.
* **Mobile First:** Responsive design optimized for students checking the menu while in line at the Dining Commons.

## 🛠️ Tech Stack
* **Frontend:** HTML5, CSS3 (Bootstrap 5), Vanilla JavaScript.
* **Backend:** Python (Flask), Gunicorn.
* **Reverse Proxy:** Nginx (configured for SSL via Certbot/Let's Encrypt).
* **Infrastructure:** Hosted in an LXC container on a Proxmox VE home lab.
* **Data:** Custom Python scraper utilizing Pandas for CSV processing and JSON for lightweight database storage.

## 📊 Logic & Methodology
### The "Protein+" Formula
To prevent "false positives" (like mushrooms or celery appearing as high protein due to low calories), we implemented a two-stage gate:
1. **Density:** $\frac{Protein(g) \times 4}{Total Calories} \ge 10\%$
2. **Substance:** Must contain at least **5g** of total protein per serving.



### Cost Estimation
Prices are derived from average wholesale bulk data. While actual University costs vary, this provides a consistent baseline for comparing the relative value of a "McFraser Sandwich" vs. a bowl of cereal.

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/pispike/eatthemargins.git](https://github.com/pispike/eatthemargins.git)
   cd eatthemargins
