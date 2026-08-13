# Logistics Operations Portal

A multi-page Streamlit dashboard for a synthetic Bangladesh e-commerce
logistics network — shipments, inventory, and delivery performance
across 5 warehouses and 5 courier partners.

**Live app:** _add your Streamlit Community Cloud URL here after deploying_

## Pages

- **Overview** — KPI cards (on-time rate, avg delivery time, shipping cost, active delays), shipment volume + on-time trend, status breakdown, shipments by region.
- **Shipments** — filterable, searchable shipment-level table with CSV export.
- **Inventory** — stock levels by warehouse/category, low-stock alerts.
- **Analytics** — on-time rate by carrier, delivery time by region, delay-reason breakdown, cost trends.

## Data

All data in `data/*.csv` is synthetically generated (`data/generate_data.py`,
seeded for reproducibility) — no real customer or shipment data is used.
Re-run the generator to refresh the dataset:

```bash
python data/generate_data.py
```

## Run locally

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows
# source .venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
streamlit run app.py
```

## Stack

Streamlit · Pandas · NumPy · Plotly
