import pandas as pd
import streamlit as st

from utils.animated_metric import animated_kpi_row
from utils.data_loader import load_first_mile
from utils.theme import apply_theme, page_title

apply_theme()

page_title(
    "📥",
    "First Mile Processing",
    "Seller pickup performance — from request to hub intake.",
)

df = load_first_mile()

# ---------- horizontal filter bar ---------- #
with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        origin_hub = st.selectbox("🏭 Origin Hub", ["All"] + sorted(df["origin_hub"].unique()))
    with c2:
        carrier = st.selectbox("🚚 Carrier", ["All"] + sorted(df["carrier"].unique()))
    with c3:
        pickup_status = st.selectbox("🏷️ Pickup Status", ["All"] + sorted(df["pickup_status"].unique()))
    with c4:
        min_date, max_date = df["request_date"].min().date(), df["request_date"].max().date()
        date_range = st.date_input("📅 Select Date", value=(min_date, max_date), min_value=min_date, max_value=max_date)

    c5, c6, c7 = st.columns([1, 1.4, 1.6])
    with c5:
        seller_region = st.selectbox("🌍 Seller Region", ["All"] + sorted(df["seller_region"].unique()))
    with c6:
        weight_lo, weight_hi = float(df["weight_kg"].min()), float(df["weight_kg"].max())
        weight_range = st.slider("⚖️ Weight (kg)", min_value=weight_lo, max_value=weight_hi, value=(weight_lo, weight_hi))
    with c7:
        search = st.text_input("🔍 Search shipment / order / package ID")

filtered = df.copy()
if origin_hub != "All":
    filtered = filtered[filtered["origin_hub"] == origin_hub]
if carrier != "All":
    filtered = filtered[filtered["carrier"] == carrier]
if pickup_status != "All":
    filtered = filtered[filtered["pickup_status"] == pickup_status]
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
    filtered = filtered[(filtered["request_date"].dt.date >= start) & (filtered["request_date"].dt.date <= end)]
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

total_requests = len(filtered)
completed = filtered[filtered["pickup_status"] == "Completed"]
success_rate = (len(completed) / total_requests * 100) if total_requests else 0.0
avg_pickup_hours = completed["pickup_duration_hours"].mean() if len(completed) else 0.0
failed = (filtered["pickup_status"] == "Failed").sum()
pending = (filtered["pickup_status"] == "Pending").sum()

animated_kpi_row(
    [
        {"label": "Total Pickup Requests", "value": total_requests},
        {"label": "Pickup Success Rate", "value": round(success_rate, 1), "decimals": 1, "suffix": "%"},
        {"label": "Avg Pickup Time", "value": round(avg_pickup_hours, 1), "decimals": 1, "suffix": " hrs"},
        {"label": "Failed Pickups", "value": int(failed)},
        {"label": "Pending Pickups", "value": int(pending)},
    ]
)

st.write("")

left, right = st.columns([1, 1.6])

with left:
    with st.container(border=True):
        st.subheader("Avg. Pickup Time by Origin Hub")
        by_hub = (
            filtered[filtered["pickup_status"].isin(["Completed", "Failed"])]
            .groupby("origin_hub")["pickup_duration_hours"]
            .mean()
            .sort_values(ascending=False)
            .round(2)
            .reset_index()
        )
        by_hub.columns = ["Origin Hub", "Pickup Time (Hours)"]
        max_hours = float(by_hub["Pickup Time (Hours)"].max()) if len(by_hub) else 1.0
        by_hub.loc[len(by_hub)] = [
            "Total",
            round(filtered[filtered["pickup_status"].isin(["Completed", "Failed"])]["pickup_duration_hours"].mean(), 2),
        ]

        st.dataframe(
            by_hub,
            column_config={
                "Pickup Time (Hours)": st.column_config.ProgressColumn(
                    "Pickup Time (Hours)", format="%.2f", min_value=0, max_value=max_hours
                )
            },
            use_container_width=True,
            hide_index=True,
            height=460,
        )

with right:
    with st.container(border=True):
        st.subheader("Pickup Time by Origin Hub × Carrier (Hour)")
        pivot = pd.pivot_table(
            filtered[filtered["pickup_status"].isin(["Completed", "Failed"])],
            index="origin_hub",
            columns="carrier",
            values="pickup_duration_hours",
            aggfunc="mean",
            margins=True,
            margins_name="Total",
        ).round(2)
        st.dataframe(pivot, use_container_width=True, height=460)

with st.container(border=True):
    st.subheader("Pickup status by carrier")
    status_by_carrier = pd.pivot_table(
        filtered,
        index="carrier",
        columns="pickup_status",
        values="request_date",
        aggfunc="count",
        fill_value=0,
        margins=True,
        margins_name="Total",
    )
    st.dataframe(status_by_carrier, use_container_width=True)
