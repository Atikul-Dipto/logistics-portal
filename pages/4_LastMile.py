import pandas as pd
import streamlit as st

from utils.data_loader import load_last_mile
from utils.theme import apply_theme, page_title

apply_theme()

page_title(
    "⏱️",
    "Last Mile Processing",
    "Pending-to-delivered processing time by hub, warehouse, and carrier.",
)

df = load_last_mile()

# ---------- horizontal filter bar ---------- #
with st.container(border=True):
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        origin_warehouse = st.selectbox("🏭 Origin Warehouse", ["All"] + sorted(df["origin_warehouse"].unique()))
    with c2:
        destination_hub = st.selectbox("📍 Destination Hub", ["All"] + sorted(df["destination_hub"].unique()))
    with c3:
        carrier = st.selectbox("🚚 Carrier", ["All"] + sorted(df["carrier"].unique()))
    with c4:
        status = st.selectbox("🏷️ Status", ["All"] + sorted(df["status"].unique()))
    with c5:
        min_date, max_date = df["order_date"].min().date(), df["order_date"].max().date()
        date_range = st.date_input("📅 Select Date", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    c6, c7, c8 = st.columns([1, 1.4, 1.6])
    with c6:
        seller_region = st.selectbox("🌍 Seller Region", ["All"] + sorted(df["seller_region"].unique()))
    with c7:
        weight_lo, weight_hi = float(df["weight_kg"].min()), float(df["weight_kg"].max())
        weight_range = st.slider("⚖️ Weight (kg)", min_value=weight_lo, max_value=weight_hi, value=(weight_lo, weight_hi))
    with c8:
        search = st.text_input("🔍 Search shipment / order / package ID")

filtered = df.copy()
if origin_warehouse != "All":
    filtered = filtered[filtered["origin_warehouse"] == origin_warehouse]
if destination_hub != "All":
    filtered = filtered[filtered["destination_hub"] == destination_hub]
if carrier != "All":
    filtered = filtered[filtered["carrier"] == carrier]
if status != "All":
    filtered = filtered[filtered["status"] == status]
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
    filtered = filtered[(filtered["order_date"].dt.date >= start) & (filtered["order_date"].dt.date <= end)]
if seller_region != "All":
    filtered = filtered[filtered["seller_region"] == seller_region]
filtered = filtered[(filtered["weight_kg"] >= weight_range[0]) & (filtered["weight_kg"] <= weight_range[1])]
if search:
    needle = search.strip().upper()
    filtered = filtered[
        filtered["shipment_id"].str.upper().str.contains(needle)
        | filtered["order_code"].str.upper().str.contains(needle)
        | filtered["package_code"].str.upper().str.contains(needle)
    ]

st.write("")

left, right = st.columns([1, 1.6])

with left:
    with st.container(border=True):
        st.subheader("Avg. Processing Time")
        by_hub = (
            filtered.groupby("destination_hub")["pending_to_delivered_hours"]
            .mean()
            .sort_values(ascending=False)
            .round(2)
            .reset_index()
        )
        by_hub.columns = ["Destination Hub", "Pending to Delivered (Hours)"]
        max_hours = float(by_hub["Pending to Delivered (Hours)"].max())  # rows are pre-sorted desc, before the Total row is appended below
        by_hub.loc[len(by_hub)] = ["Total", round(filtered["pending_to_delivered_hours"].mean(), 2)]

        st.dataframe(
            by_hub,
            column_config={
                "Pending to Delivered (Hours)": st.column_config.ProgressColumn(
                    "Pending to Delivered (Hours)", format="%.2f", min_value=0, max_value=max_hours
                )
            },
            use_container_width=True,
            hide_index=True,
            height=460,
        )

with right:
    with st.container(border=True):
        st.subheader("Last Mile Processing Time by Destination Hub × Carrier (Hour)")
        pivot_hub = pd.pivot_table(
            filtered,
            index="destination_hub",
            columns="carrier",
            values="pending_to_delivered_hours",
            aggfunc="mean",
            margins=True,
            margins_name="Total",
        ).round(2)
        st.dataframe(pivot_hub, use_container_width=True, height=460)

with st.container(border=True):
    st.subheader("Last Mile Processing Time by Origin Warehouse × Destination Hub (Hour)")
    pivot_warehouse = pd.pivot_table(
        filtered,
        index="origin_warehouse",
        columns="destination_hub",
        values="pending_to_delivered_hours",
        aggfunc="mean",
        margins=True,
        margins_name="Total",
    ).round(2)
    st.dataframe(pivot_warehouse, use_container_width=True)
