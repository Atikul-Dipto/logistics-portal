import pandas as pd
import streamlit as st

from utils.data_loader import load_last_mile
from utils.theme import apply_theme, page_title

apply_theme()

page_title(
    "⏱️",
    "Last Mile Processing",
    "Pending-to-delivered processing time by hub, fleet type, and shipping zone.",
)

df = load_last_mile()

# ---------- horizontal filter bar ---------- #
with st.container(border=True):
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1:
        source_hub = st.selectbox("🏭 Source Hub", ["All"] + sorted(df["source_hub"].unique()))
    with c2:
        destination_hub = st.selectbox("📍 Destination Hub", ["All"] + sorted(df["destination_hub"].unique()))
    with c3:
        shipping_state = st.selectbox("🗺️ Shipping State", ["All"] + sorted(df["shipping_state"].unique()))
    with c4:
        shipping_city = st.selectbox("🏙️ Shipping City", ["All"] + sorted(df["shipping_city"].unique()))
    with c5:
        shipping_zone = st.selectbox("🧭 Shipping Zone", ["All"] + sorted(df["shipping_zone"].unique()))
    with c6:
        fleet_type = st.selectbox("🚛 Fleet Type", ["All"] + sorted(df["fleet_type"].unique()))
    with c7:
        min_date, max_date = df["order_date"].min().date(), df["order_date"].max().date()
        date_range = st.date_input("📅 Select Date", value=(min_date, max_date), min_value=min_date, max_value=max_date)

filtered = df.copy()
if source_hub != "All":
    filtered = filtered[filtered["source_hub"] == source_hub]
if destination_hub != "All":
    filtered = filtered[filtered["destination_hub"] == destination_hub]
if shipping_state != "All":
    filtered = filtered[filtered["shipping_state"] == shipping_state]
if shipping_city != "All":
    filtered = filtered[filtered["shipping_city"] == shipping_city]
if shipping_zone != "All":
    filtered = filtered[filtered["shipping_zone"] == shipping_zone]
if fleet_type != "All":
    filtered = filtered[filtered["fleet_type"] == fleet_type]
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
    filtered = filtered[(filtered["order_date"].dt.date >= start) & (filtered["order_date"].dt.date <= end)]

st.write("")

left, right = st.columns([1, 1.6])

with left:
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
    st.subheader("Last Mile Processing Time by Destination Hub (Hour)")
    pivot_hub = pd.pivot_table(
        filtered,
        index="destination_hub",
        columns="shipping_zone",
        values="pending_to_delivered_hours",
        aggfunc="mean",
        margins=True,
        margins_name="Total",
    ).round(2)
    st.dataframe(pivot_hub, use_container_width=True, height=460)

st.subheader("Last Mile Processing Time by Fleet Type (Hour)")
pivot_fleet = pd.pivot_table(
    filtered,
    index="fleet_type",
    columns="shipping_zone",
    values="pending_to_delivered_hours",
    aggfunc="mean",
    margins=True,
    margins_name="Total",
).round(2)
st.dataframe(pivot_fleet, use_container_width=True)
