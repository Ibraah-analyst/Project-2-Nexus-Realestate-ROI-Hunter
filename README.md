# 🚀 Project Nexus: Real Estate ROI Hunter
**Automated Intelligence Engine for High-Alpha Property Detection**

## 🎯 Executive Summary
Project Nexus is a custom-built Business Intelligence (BI) engine designed to solve the "fragmented data" problem in real estate. By synchronizing with live market APIs, the engine scans thousands of listings across Austin, Miami, Houston, Phoenix, and Las Vegas to mathematically isolate "Unicorn" deals—properties priced significantly below their market value.



## 🛠️ The Nexus Pipeline (Technical Process)
1. **Data Synchronization:** Direct REST API handshake with Realtor-in-US endpoints to pull high-fidelity JSON data.
2. **Gold-Sieve Cleaning:** Automated imputation of missing coordinates and square footage using city-level medians.
3. **Alpha Feature Engineering:** Implementation of Z-Score analysis to calculate the "Value Gap" (List Price vs. City Mean).
4. **Investment Tiering:** Algorithmic categorization into **TIER 1: UNICORN**, **TIER 2: EQUITY KING**, and **TIER 3: VALUE LEADER**.
5. **Interactive BI:** A standalone JavaScript-integrated HTML dashboard for real-time portfolio filtering.

## 📊 Key Deliverables
* **Nexus_Executive_Dashboard.html:** An interactive dashboard for non-technical stakeholders.
* **Nexus_PRIME_Investment_Targets.csv:** A filtered list of the top 15% of high-ROI assets.
* **Automation Suite:** Python scripts ready for daily scheduling via Cron (Mac) or Task Scheduler (Win).

## 🚀 How to Run & Automate
### Installation
```bash
pip install pandas requests plotly seaborn
