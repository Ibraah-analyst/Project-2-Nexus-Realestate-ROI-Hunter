import pandas as pd
import numpy as np
import requests
import datetime
import time
import base64
import os
import warnings
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
from io import BytesIO
import json # Added to handle data transfer to JavaScript

# --- 0. CONFIGURATION & STANDARDS ---
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)
pd.options.mode.chained_assignment = None 

MY_API_KEY = os.getenv("REALTY_API_KEY")
ENDPOINT_URL = "https://realty-in-us.p.rapidapi.com/properties/v3/list"
HEADERS = {"X-RapidAPI-Key": MY_API_KEY, "X-RapidAPI-Host": "realty-in-us.p.rapidapi.com"}

# The 5 Primary Hubs (Strict Enforcement)
TARGET_CITIES = ["Austin", "Houston", "Miami", "Phoenix", "Las Vegas"]
TARGET_MARKETS = [
    {"city": "Austin", "state": "TX"}, {"city": "Miami", "state": "FL"},
    {"city": "Houston", "state": "TX"}, {"city": "Phoenix", "state": "AZ"},
    {"city": "Las Vegas", "state": "NV"}
]

def run_nexus_automation():
    # Define start_time early so it can be used in the Dashboard
    run_timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    print(f"🚀 STARTING NEXUS HIGH-FIDELITY ENGINE | {run_timestamp}")

    # --- PHASE 1: DATA ACQUISITION ---
    raw_list = []
    for market in TARGET_MARKETS:
        print(f"📡 API Pull: {market['city']}...")
        payload = {"limit": 200, "city": market["city"], "state_code": market["state"], "status": ["for_sale"]}
        try:
            res = requests.post(ENDPOINT_URL, json=payload, headers=HEADERS, timeout=30)
            if res.status_code == 200:
                raw_list.extend(res.json().get("data", {}).get("home_search", {}).get("results", []))
        except: pass
        time.sleep(1.1)

    df_raw = pd.json_normalize(raw_list)
    cols_to_keep = [
        "property_id", "location.address.city", "location.address.postal_code", "location.address.state_code",
        "location.address.coordinate.lat", "location.address.coordinate.lon",
        "description.type", "description.sqft", "description.lot_sqft",
        "description.beds", "description.baths", "list_price",
        "estimate.estimate", "flags.is_price_reduced", "flags.is_foreclosure",
        "flags.is_new_listing", "price_reduced_amount", "list_date",
        "last_sold_price", "href"
    ]
    existing_cols = [c for c in cols_to_keep if c in df_raw.columns]
    df_raw = df_raw[existing_cols]
    df_raw.to_csv("Nexus_RAW_Data.csv", index=False)

    # --- PHASE 2: HIGH-FIDELITY CLEANING ---
    print("🧹 EXECUTING HIGH-FIDELITY CLEANING...")
    df_clean = df_raw[df_raw["location.address.city"].isin(TARGET_CITIES)].copy()
    df_clean = df_clean.dropna(subset=["description.sqft", "list_price"])
    
    for coord in ["location.address.coordinate.lat", "location.address.coordinate.lon"]:
        if coord in df_clean.columns:
            df_clean[coord] = df_clean.groupby("location.address.city")[coord].transform(lambda x: x.fillna(x.mean()))
    
    df_clean["description.beds"] = df_clean["description.beds"].fillna(df_clean["description.beds"].median())
    df_clean["description.baths"] = df_clean["description.baths"].fillna(df_clean["description.baths"].median())

    df_clean["flags.is_price_reduced"] = df_clean.get("flags.is_price_reduced", pd.Series(dtype=bool)).fillna(False).astype(bool)
    df_clean["flags.is_foreclosure"] = df_clean.get("flags.is_foreclosure", pd.Series(dtype=bool)).fillna(False).astype(bool)
    df_clean["list_date"] = pd.to_datetime(df_clean["list_date"], errors='coerce')
    df_clean = df_clean.drop_duplicates(subset=["property_id"])
    df_clean = df_clean[df_clean["list_price"] > 50000] 
    
    df_clean.to_csv("Nexus_Gold_Cleaned.csv", index=False)

    # --- PHASE 3: FEATURE ENGINEERING & ROI ---
    print("💎 GENERATING NEXUS PRIME INTELLIGENCE...")
    df_bi = df_clean.copy()
    
    df_bi["price_per_sqft"] = df_bi["list_price"] / df_bi["description.sqft"]
    stats = df_bi.groupby("location.address.city")["price_per_sqft"].agg(["mean", "std"]).reset_index()
    stats.columns = ["location.address.city", "city_mean", "city_std"]
    df_bi = df_bi.merge(stats, on="location.address.city", how="left")
    
    df_bi["value_gap_pct"] = (df_bi["city_mean"] - df_bi["price_per_sqft"]) / df_bi["city_mean"]
    df_bi["market_z_score"] = (df_bi["price_per_sqft"] - df_bi["city_mean"]) / df_bi["city_std"]
    df_bi["is_investment_grade"] = df_bi["market_z_score"] < 0
    
    df_bi["nexus_alpha_score"] = (df_bi["value_gap_pct"] * 100).clip(0, 100)
    
    df_bi["equity_gap_pct"] = (df_bi["estimate.estimate"] - df_bi["list_price"]) / df_bi["estimate.estimate"]
    df_bi["equity_gap_pct"] = df_bi["equity_gap_pct"].fillna(df_bi["value_gap_pct"] * 0.5)

    df_bi["deal_score"] = (
        (df_bi["value_gap_pct"].clip(0, 1) * 40) + 
        (df_bi["equity_gap_pct"].clip(0, 1) * 40) + 
        (np.abs(df_bi["market_z_score"].clip(-2, 0)) * 10)
    )

    conds = [
        (df_bi["deal_score"] >= 30) & (df_bi["is_investment_grade"] == True),
        (df_bi["equity_gap_pct"] >= 0.15),
        (df_bi["value_gap_pct"] >= 0.40)
    ]
    tiers = ["TIER 1: UNICORN", "TIER 2: EQUITY KING", "TIER 3: VALUE LEADER"]
    df_bi["investment_tier"] = np.select(conds, tiers, default="Market Standard")

    def create_thesis(row):
        if row["investment_tier"] == "TIER 1: UNICORN": return "Extreme Alpha: Deeply undervalued with high instant equity."
        if row["investment_tier"] == "TIER 2: EQUITY KING": return f"Equity Play: Priced {row['equity_gap_pct']:.1%} below estimated value."
        if row["investment_tier"] == "TIER 3: VALUE LEADER": return f"Value Play: $/SqFt is {row['value_gap_pct']:.1%} below city average."
        return "N/A"
    df_bi["investment_thesis"] = df_bi.apply(create_thesis, axis=1)

    df_bi.to_csv("Nexus_Master_Intelligence.csv", index=False)
    df_prime = df_bi[df_bi["investment_tier"] != "Market Standard"].sort_values("deal_score", ascending=False)
    df_prime.to_csv("Nexus_PRIME_Investment_Targets.csv", index=False)

    # --- PHASE 4: VISUALIZATIONS ---
    print("📊 PRODUCING BOARDROOM VISUALS...")
    def fig_to_b64(fig):
        buf = BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        return base64.b64encode(buf.getvalue()).decode("utf-8")

    total_scanned = len(df_bi)
    
    # 4.1 Price Benchmarks
    plt.figure(figsize=(8, 4))
    sns.boxplot(data=df_bi, x="location.address.city", y="price_per_sqft", hue="location.address.city", palette="Blues", legend=False)
    v1 = fig_to_b64(plt.gcf()); plt.close()

    # 4.2 Strategy Analysis
    plt.figure(figsize=(8, 4))
    sns.scatterplot(data=df_prime, x="value_gap_pct", y="equity_gap_pct", hue="investment_tier", palette="Set1")
    v2 = fig_to_b64(plt.gcf()); plt.close()

    # 4.3 Alpha Neighborhoods (Zip Codes)
    plt.figure(figsize=(8, 4))
    df_prime.groupby("location.address.postal_code")["nexus_alpha_score"].mean().sort_values().tail(10).plot(kind="barh", color="gold")
    plt.title("Top 10 High-Alpha Zip Codes")
    v3 = fig_to_b64(plt.gcf()); plt.close()

    # 4.4 Portfolio Mix
    plt.figure(figsize=(5, 5))
    df_prime["investment_tier"].value_counts().plot(kind="pie", autopct="%1.1f%%", colors=["#FFD700", "#3498DB", "#2ECC71"])
    plt.ylabel("")
    v4 = fig_to_b64(plt.gcf()); plt.close()

    # Map Creation
    fig_map = px.scatter_geo(
        df_prime, lat="location.address.coordinate.lat", lon="location.address.coordinate.lon", 
        color="investment_tier", size="deal_score", hover_name="location.address.city", scope="usa",
        color_discrete_map={"TIER 1: UNICORN": "#FFD700", "TIER 2: EQUITY KING": "#3498DB", "TIER 3: VALUE LEADER": "#2ECC71"}
    )
    map_html = fig_map.to_html(full_html=False, include_plotlyjs="cdn")

    # --- DATA PREP FOR DYNAMIC JS FILTER ---
    # Create a small JSON-ready list of our prime data for the filter to use
    prime_data_json = df_prime[['location.address.state_code', 'list_price', 'equity_gap_pct', 'value_gap_pct']].to_json(orient='records')

    # HTML ASSEMBLY WITH JAVASCRIPT FILTERING
    html_dashboard = f"""
    <html>
    <head>
        <style>
            body{{font-family:'Segoe UI', sans-serif; background:#f4f7f6; margin:40px;}}
            .summary-card{{display:flex; justify-content:space-between; background:#2c3e50; color:white; padding:20px; border-radius:10px; margin-bottom:20px;}}
            .stat-box{{text-align:center; flex:1;}}
            .box{{background:white; padding:20px; border-radius:10px; margin-bottom:20px; box-shadow:0 2px 5px rgba(0,0,0,0.1);}}
            .filter-section{{background:#ecf0f1; padding:15px; border-radius:10px; margin-bottom:20px; border: 1px solid #bdc3c7;}}
            select{{padding:10px; border-radius:5px; width: 250px; font-size:16px; cursor:pointer;}}
        </style>
        <script>
            const primeData = {prime_data_json};
            
            function updateMetrics() {{
                const selectedState = document.getElementById('stateFilter').value;
                
                // Filter data
                const filtered = selectedState === 'ALL' ? primeData : primeData.filter(d => d['location.address.state_code'] === selectedState);
                
                // Calculations
                const count = filtered.length;
                const totalVal = filtered.reduce((sum, item) => sum + item.list_price, 0);
                const avgEquity = filtered.length > 0 ? (filtered.reduce((sum, item) => sum + item.equity_gap_pct, 0) / filtered.length) * 100 : 0;
                
                // Update DOM
                document.getElementById('prime-count').innerText = count;
                document.getElementById('total-value').innerText = '$' + (totalVal / 1000000).toFixed(2) + 'M';
                document.getElementById('avg-equity').innerText = avgEquity.toFixed(1) + '%';
            }}
        </script>
    </head>
    <body onload="updateMetrics()">
        <h1 style="color:#2c3e50;">NEXUS REAL ESTATE ROI DASHBOARD</h1>
        
        <div class="filter-section">
            <label><b>LIVE MARKET FILTER: </b></label>
            <select id="stateFilter" onchange="updateMetrics()">
                <option value="ALL">All Markets (National View)</option>
                <option value="TX">Texas (Austin/Houston)</option>
                <option value="FL">Florida (Miami)</option>
                <option value="AZ">Arizona (Phoenix)</option>
                <option value="NV">Nevada (Las Vegas)</option>
            </select>
            <span style="margin-left: 20px; color: #7f8c8d;"><i>*Metrics update instantly based on selection.</i></span>
        </div>

        <div class="summary-card">
            <div class="stat-box"><h4>LAST SCAN</h4><p>{run_timestamp}</p></div>
            <div class="stat-box"><h4>TOTAL PRIME TARGETS</h4><p id="prime-count">0</p></div>
            <div class="stat-box"><h4>TOTAL PORTFOLIO VALUE</h4><p id="total-value">$0M</p></div>
            <div class="stat-box"><h4>AVG. EQUITY GAP</h4><p id="avg-equity">0%</p></div>
        </div>

        <div class="box"><h2>1. Live Spatial Intelligence Map</h2>{map_html}</div>
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:20px;">
            <div class="box"><h3>2. Price Benchmarks</h3><img src="data:image/png;base64,{v1}" width="100%"></div>
            <div class="box"><h3>3. Strategy Analysis</h3><img src="data:image/png;base64,{v2}" width="100%"></div>
            <div class="box"><h3>4. Alpha Neighborhoods (Zip)</h3><img src="data:image/png;base64,{v3}" width="100%"></div>
            <div class="box"><h3>5. Portfolio Mix</h3><img src="data:image/png;base64,{v4}" width="100%"></div>
        </div>
    </body></html>"""
    
    with open("Nexus_Executive_Dashboard.html", "w", encoding="utf-8") as f:
        f.write(html_dashboard)
    
    print(f"✅ COMPLETE: Interactive Dashboard saved. Prime Hits isolated.")

if __name__ == "__main__":
    run_nexus_automation()