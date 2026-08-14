import plotly.express as px
import streamlit as st

from utils.animated_metric import animated_kpi_row
from utils.charts import CHART_COLORS, style_fig
from utils.data_loader import compact_parts, load_shipments
from utils.live_feed import render_live_feed
from utils.theme import apply_theme, page_title

apply_theme()

PLOTLY_TEMPLATE = "plotly_dark"
ACCENT = "#5b8def"
REGION_CHART_KEY = "overview_region_chart"

page_title("📦", "Logistics Operations Portal", "Shipment, inventory, and delivery performance across a multi-warehouse network.")

render_live_feed()
st.write("")

df = load_shipments()

# ---------- sidebar filters ----------
st.sidebar.header("Filters")
min_date, max_date = df["order_date"].min().date(), df["order_date"].max().date()
date_range = st.sidebar.date_input(
    "📅 Order date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
)
warehouses = st.sidebar.multiselect("🏭 Warehouse", sorted(df["warehouse"].unique()))
carriers = st.sidebar.multiselect("🚚 Carrier", sorted(df["carrier"].unique()))
seller_regions = st.sidebar.multiselect("🌍 Seller Region", sorted(df["seller_region"].unique()))
weight_lo, weight_hi = float(df["weight_kg"].min()), float(df["weight_kg"].max())
weight_range = st.sidebar.slider("⚖️ Weight (kg)", min_value=weight_lo, max_value=weight_hi, value=(weight_lo, weight_hi))

base_filtered = df.copy()
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
    base_filtered = base_filtered[(base_filtered["order_date"].dt.date >= start) & (base_filtered["order_date"].dt.date <= end)]
if warehouses:
    base_filtered = base_filtered[base_filtered["warehouse"].isin(warehouses)]
if carriers:
    base_filtered = base_filtered[base_filtered["carrier"].isin(carriers)]
if seller_regions:
    base_filtered = base_filtered[base_filtered["seller_region"].isin(seller_regions)]
base_filtered = base_filtered[(base_filtered["weight_kg"] >= weight_range[0]) & (base_filtered["weight_kg"] <= weight_range[1])]

# clicking a bar in "Shipments by destination region" below cross-filters
# the KPIs and the two charts above it, Power-BI style
region_selection = st.session_state.get(REGION_CHART_KEY, {}).get("selection", {}).get("points", [])
clicked_region = region_selection[0]["x"] if region_selection else None

filtered = base_filtered.copy()
if clicked_region:
    filtered = filtered[filtered["destination_region"] == clicked_region]

# ---------- KPI row ----------
total_shipments = len(filtered)
delivered = filtered[filtered["is_delivered"]]
on_time_rate = delivered["on_time"].mean() * 100 if len(delivered) else 0.0
avg_delivery_days = delivered["delivery_days"].mean() if len(delivered) else 0.0
total_cost = filtered["shipping_cost"].sum()
active_delayed = filtered[filtered["status"] == "Delayed"].shape[0]

if clicked_region:
    badge_l, badge_r = st.columns([5, 1])
    with badge_l:
        st.caption(f"🔎 Filtered to **{clicked_region}** (click the bar again or clear to reset)")
    with badge_r:
        if st.button("✕ Clear", use_container_width=True):
            st.session_state.pop(REGION_CHART_KEY, None)
            st.rerun()

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
    with st.container(border=True):
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
        )
        st.plotly_chart(style_fig(fig), use_container_width=True)

with right:
    with st.container(border=True):
        st.subheader("Status breakdown")
        status_counts = filtered["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]
        fig2 = px.pie(
            status_counts,
            names="status",
            values="count",
            hole=0.55,
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=CHART_COLORS,
        )
        st.plotly_chart(style_fig(fig2), use_container_width=True)

with st.container(border=True):
    st.subheader("Shipments by destination region")
    st.caption("Click a bar to filter the whole page by that region — click again to change it, or clear above.")
    region = base_filtered.groupby("destination_region")["shipment_id"].count().sort_values(ascending=False).reset_index()
    region.columns = ["region", "shipments"]
    fig3 = px.bar(region, x="region", y="shipments", template=PLOTLY_TEMPLATE, color_discrete_sequence=[ACCENT])
    fig3.update_layout(clickmode="event+select")
    st.plotly_chart(
        style_fig(fig3),
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        key=REGION_CHART_KEY,
    )
