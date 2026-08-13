import streamlit as st

from utils.data_loader import load_shipments
from utils.theme import apply_theme

st.set_page_config(page_title="Logistics Portal · Shipments", page_icon="🚚", layout="wide")
apply_theme()

st.title("🚚 Shipments")
st.caption("Search, filter, and inspect individual shipments across the network.")

df = load_shipments()

st.sidebar.header("Filters")
status = st.sidebar.multiselect("Status", sorted(df["status"].unique()))
warehouse = st.sidebar.multiselect("Warehouse", sorted(df["warehouse"].unique()))
carrier = st.sidebar.multiselect("Carrier", sorted(df["carrier"].unique()))
region = st.sidebar.multiselect("Destination region", sorted(df["destination_region"].unique()))
search = st.sidebar.text_input("Search shipment ID or SKU")

filtered = df.copy()
if status:
    filtered = filtered[filtered["status"].isin(status)]
if warehouse:
    filtered = filtered[filtered["warehouse"].isin(warehouse)]
if carrier:
    filtered = filtered[filtered["carrier"].isin(carrier)]
if region:
    filtered = filtered[filtered["destination_region"].isin(region)]
if search:
    needle = search.strip().upper()
    filtered = filtered[
        filtered["shipment_id"].str.upper().str.contains(needle)
        | filtered["sku"].str.upper().str.contains(needle)
    ]

st.write(f"**{len(filtered):,}** shipments match your filters.")

STATUS_COLOR = {
    "Delivered": "🟢",
    "Delivered Late": "🟠",
    "In Transit": "🔵",
    "Delayed": "🟠",
    "Cancelled": "⚪",
    "Returned": "🔴",
}
display = filtered.copy()
display["status"] = display["status"].map(lambda s: f"{STATUS_COLOR.get(s, '')} {s}")

st.dataframe(
    display[
        [
            "shipment_id",
            "order_date",
            "warehouse",
            "destination_region",
            "carrier",
            "product",
            "qty",
            "shipping_cost",
            "status",
            "expected_delivery",
            "actual_delivery",
            "delay_reason",
        ]
    ].sort_values("order_date", ascending=False),
    use_container_width=True,
    height=560,
    hide_index=True,
)

csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button("Download filtered results (CSV)", csv, "shipments_filtered.csv", "text/csv")
