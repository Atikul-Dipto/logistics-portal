import plotly.express as px
import streamlit as st

from utils.animated_metric import animated_kpi_row
from utils.data_loader import compact_parts, load_shipments
from utils.theme import apply_theme, page_title

st.set_page_config(page_title="Logistics Portal · Overview", page_icon="📦", layout="wide")
apply_theme()

PLOTLY_TEMPLATE = "plotly_dark"
ACCENT = "#5b8def"

page_title("📦", "Logistics Operations Portal", "Shipment, inventory, and delivery performance across a multi-warehouse network.")

df = load_shipments()

# ---------- sidebar filters ----------
st.sidebar.header("Filters")
min_date, max_date = df["order_date"].min().date(), df["order_date"].max().date()
date_range = st.sidebar.date_input(
    "📅 Order date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)
warehouses = st.sidebar.multiselect("🏭 Warehouse", sorted(df["warehouse"].unique()))
carriers = st.sidebar.multiselect("🚚 Carrier", sorted(df["carrier"].unique()))

filtered = df.copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
    filtered = filtered[(filtered["order_date"].dt.date >= start) & (filtered["order_date"].dt.date <= end)]
if warehouses:
    filtered = filtered[filtered["warehouse"].isin(warehouses)]
if carriers:
    filtered = filtered[filtered["carrier"].isin(carriers)]

# ---------- KPI row ----------
total_shipments = len(filtered)
delivered = filtered[filtered["is_delivered"]]
on_time_rate = delivered["on_time"].mean() * 100 if len(delivered) else 0.0
avg_delivery_days = delivered["delivery_days"].mean() if len(delivered) else 0.0
total_cost = filtered["shipping_cost"].sum()
active_delayed = filtered[filtered["status"] == "Delayed"].shape[0]

cost_amount, cost_suffix = compact_parts(total_cost)
animated_kpi_row(
    [
        {"label": "Total Shipments", "value": total_shipments},
        {"label": "On-Time Delivery", "value": round(on_time_rate, 1), "decimals": 1, "suffix": "%"},
        {"label": "Avg Delivery Time", "value": round(avg_delivery_days, 1), "decimals": 1, "suffix": " days"},
        {"label": "Total Shipping Cost", "value": cost_amount, "prefix": "BDT ", "suffix": cost_suffix},
        {"label": "Active Delays", "value": active_delayed},
    ]
)

st.divider()

# ---------- trend charts ----------
left, right = st.columns([1.4, 1])

with left:
    st.subheader("Shipment volume & on-time rate over time")
    monthly = (
        filtered.groupby("order_month")
        .agg(shipments=("shipment_id", "count"), on_time_rate=("on_time", "mean"))
        .reset_index()
    )
    monthly["on_time_rate"] *= 100

    fig = px.bar(monthly, x="order_month", y="shipments", template=PLOTLY_TEMPLATE)
    fig.update_traces(marker_color=ACCENT, name="Shipments", showlegend=True)
    fig.add_scatter(
        x=monthly["order_month"],
        y=monthly["on_time_rate"],
        mode="lines+markers",
        name="On-time %",
        yaxis="y2",
        line=dict(color="#22d3ee", width=3),
    )
    fig.update_layout(
        yaxis=dict(title="Shipments"),
        yaxis2=dict(title="On-time %", overlaying="y", side="right", range=[0, 100]),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("Status breakdown")
    status_counts = filtered["status"].value_counts().reset_index()
    status_counts.columns = ["status", "count"]
    fig2 = px.pie(
        status_counts,
        names="status",
        values="count",
        hole=0.55,
        template=PLOTLY_TEMPLATE,
        color_discrete_sequence=["#5b8def", "#22d3ee", "#7c3aed", "#f59e0b", "#ef4444", "#64748b"],
    )
    fig2.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig2, use_container_width=True)

st.subheader("Shipments by destination region")
region = filtered.groupby("destination_region")["shipment_id"].count().sort_values(ascending=False).reset_index()
region.columns = ["region", "shipments"]
fig3 = px.bar(region, x="region", y="shipments", template=PLOTLY_TEMPLATE, color_discrete_sequence=[ACCENT])
fig3.update_layout(margin=dict(t=10, b=10))
st.plotly_chart(fig3, use_container_width=True)
