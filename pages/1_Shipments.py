import streamlit as st

from utils.data_loader import load_shipments
from utils.theme import apply_theme, page_title

apply_theme()

page_title("🚚", "Shipments", "Search, filter, and inspect individual shipments across the network.")

df = load_shipments()

st.sidebar.header("Filters")
status = st.sidebar.multiselect("🏷️ Status", sorted(df["status"].unique()))
warehouse = st.sidebar.multiselect("🏭 Warehouse", sorted(df["warehouse"].unique()))
carrier = st.sidebar.multiselect("🚚 Carrier", sorted(df["carrier"].unique()))
region = st.sidebar.multiselect("📍 Destination region", sorted(df["destination_region"].unique()))
seller_region = st.sidebar.multiselect("🌍 Seller Region", sorted(df["seller_region"].unique()))
shop_name = st.sidebar.multiselect("🏪 Shop Name", sorted(df["shop_name"].unique()))
seller_code = st.sidebar.multiselect("🔖 Seller Code", sorted(df["seller_code"].unique()))
weight_lo, weight_hi = float(df["weight_kg"].min()), float(df["weight_kg"].max())
weight_range = st.sidebar.slider("⚖️ Weight (kg)", min_value=weight_lo, max_value=weight_hi, value=(weight_lo, weight_hi))
search = st.sidebar.text_input("🔍 Search shipment / order / package ID or SKU")

filtered = df.copy()
if status:
    filtered = filtered[filtered["status"].isin(status)]
if warehouse:
    filtered = filtered[filtered["warehouse"].isin(warehouse)]
if carrier:
    filtered = filtered[filtered["carrier"].isin(carrier)]
if region:
    filtered = filtered[filtered["destination_region"].isin(region)]
if seller_region:
    filtered = filtered[filtered["seller_region"].isin(seller_region)]
if shop_name:
    filtered = filtered[filtered["shop_name"].isin(shop_name)]
if seller_code:
    filtered = filtered[filtered["seller_code"].isin(seller_code)]
filtered = filtered[(filtered["weight_kg"] >= weight_range[0]) & (filtered["weight_kg"] <= weight_range[1])]
if search:
    needle = search.strip().upper()
    filtered = filtered[
        filtered["shipment_id"].str.upper().str.contains(needle)
        | filtered["order_code"].str.upper().str.contains(needle)
        | filtered["package_code"].str.upper().str.contains(needle)
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

with st.container(border=True):
    st.dataframe(
        display[
            [
                "shipment_id",
                "order_code",
                "package_code",
                "order_date",
                "warehouse",
                "shop_name",
                "seller_region",
                "destination_region",
                "carrier",
                "product",
                "qty",
                "weight_kg",
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
