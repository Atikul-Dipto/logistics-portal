import plotly.express as px
import streamlit as st

from utils.animated_metric import animated_kpi_row
from utils.charts import CHART_COLORS, style_fig
from utils.data_loader import compact_parts, load_bd_divisions_geojson, load_shipments
from utils.live_feed import render_live_feed
from utils.theme import apply_theme, page_title

apply_theme()

PLOTLY_TEMPLATE = "plotly_dark"
ACCENT = "#5b8def"
REGION_CHART_KEY = "overview_region_chart"
MAP_CHART_KEY = "overview_map_chart"

# our destination_region values -> the 8 official divisions in
# data/bd_divisions.geojson. Comilla and Narayanganj are districts
# (not divisions) so their volume rolls up into their parent
# division on the map; every other page keeps the finer 10-region
# breakdown.
DIVISION_MAP = {
    "Dhaka": "Dhaka",
    "Chattogram": "Chattogram",
    "Sylhet": "Sylhet",
    "Khulna": "Khulna",
    "Rajshahi": "Rajshahi",
    "Barisal": "Barishal",
    "Rangpur": "Rangpur",
    "Mymensingh": "Mymensingh",
    "Comilla": "Chattogram",
    "Narayanganj": "Dhaka",
}
DIVISION_ORDER = sorted(set(DIVISION_MAP.values()))

page_title("📦", "Logistics Operations Portal", "Shipment, inventory, and delivery performance across a multi-warehouse network.")

render_live_feed()
st.write("")

df = load_shipments()

# ---------- filter bar ---------- #
with st.container(border=True):
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        min_date, max_date = df["order_date"].min().date(), df["order_date"].max().date()
        date_range = st.date_input("📅 Order date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    with c2:
        warehouses = st.multiselect("🏭 Warehouse", sorted(df["warehouse"].unique()))
    with c3:
        carriers = st.multiselect("🚚 Carrier", sorted(df["carrier"].unique()))
    with c4:
        seller_regions = st.multiselect("🌍 Seller Region", sorted(df["seller_region"].unique()))
    with c5:
        weight_lo, weight_hi = float(df["weight_kg"].min()), float(df["weight_kg"].max())
        weight_range = st.slider("⚖️ Weight (kg)", min_value=weight_lo, max_value=weight_hi, value=(weight_lo, weight_hi))

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

# clicking the map or the region bar chart below cross-filters the
# KPIs and the two charts above them, Power-BI style — the map wins
# if both happen to be set, since it's the more prominent control.
# The map clicks a *division* (8, grouping Comilla into Chattogram
# and Narayanganj into Dhaka); the bar clicks an exact *region* (10).
region_selection = st.session_state.get(REGION_CHART_KEY, {}).get("selection", {}).get("points", [])
bar_clicked_region = region_selection[0]["x"] if region_selection else None

map_selection = st.session_state.get(MAP_CHART_KEY, {}).get("selection", {}).get("points", [])
map_clicked_division = None
if map_selection and "point_index" in map_selection[0]:
    idx = map_selection[0]["point_index"]
    if idx < len(DIVISION_ORDER):
        map_clicked_division = DIVISION_ORDER[idx]

filtered = base_filtered.copy()
if map_clicked_division:
    clicked_label = map_clicked_division
    filtered = filtered[filtered["destination_region"].map(DIVISION_MAP) == map_clicked_division]
elif bar_clicked_region:
    clicked_label = bar_clicked_region
    filtered = filtered[filtered["destination_region"] == bar_clicked_region]
else:
    clicked_label = None

# ---------- KPI row ----------
total_shipments = len(filtered)
delivered = filtered[filtered["is_delivered"]]
on_time_rate = delivered["on_time"].mean() * 100 if len(delivered) else 0.0
avg_delivery_days = delivered["delivery_days"].mean() if len(delivered) else 0.0
total_cost = filtered["shipping_cost"].sum()
active_delayed = filtered[filtered["status"] == "Delayed"].shape[0]

if clicked_label:
    badge_l, badge_r = st.columns([5, 1])
    with badge_l:
        st.caption(f"🔎 Filtered to **{clicked_label}** (click the map or bar again to change it, or clear)")
    with badge_r:
        if st.button("✕ Clear", use_container_width=True):
            st.session_state.pop(REGION_CHART_KEY, None)
            st.session_state.pop(MAP_CHART_KEY, None)
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
    st.subheader("Network map — shipment volume by division")
    st.caption("Color = shipment volume. Click a division to filter the whole page by it — Comilla and Narayanganj roll up into their parent division here.")
    geojson = load_bd_divisions_geojson()

    map_df = base_filtered.copy()
    map_df["division"] = map_df["destination_region"].map(DIVISION_MAP)
    map_agg = (
        map_df.groupby("division")
        .agg(shipments=("shipment_id", "count"), on_time_rate=("on_time", "mean"))
        .reindex(DIVISION_ORDER, fill_value=0)
        .reset_index()
    )
    map_agg["on_time_rate"] = (map_agg["on_time_rate"] * 100).round(1)

    fig_map = px.choropleth(
        map_agg,
        geojson=geojson,
        locations="division",
        featureidkey="properties.division",
        color="shipments",
        color_continuous_scale=[[0, "#1c2333"], [0.5, "#3a5aa8"], [1, "#5b8def"]],
        hover_name="division",
        hover_data={"shipments": True, "on_time_rate": ":.1f", "division": False},
    )
    fig_map.update_traces(
        marker_line_color="rgba(238,242,255,0.75)",
        marker_line_width=1,
        # Plotly dims every unselected shape by default once one is
        # clicked, which washes the whole map to one flat tone —
        # keep every division at full color regardless of selection.
        selected=dict(marker=dict(opacity=1)),
        unselected=dict(marker=dict(opacity=1)),
    )
    fig_map.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig_map.update_layout(height=560, coloraxis_colorbar=dict(title="Shipments"))
    st.plotly_chart(
        style_fig(fig_map),
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        key=MAP_CHART_KEY,
    )

with st.container(border=True):
    st.subheader("Shipments by destination region")
    st.caption("Click a bar to filter the whole page by that region — click again to change it, or clear above.")
    region = base_filtered.groupby("destination_region")["shipment_id"].count().sort_values(ascending=False).reset_index()
    region.columns = ["region", "shipments"]
    fig3 = px.bar(region, x="region", y="shipments", template=PLOTLY_TEMPLATE, color_discrete_sequence=[ACCENT])
    fig3.update_layout(clickmode="event+select")
    fig3.update_traces(selected=dict(marker=dict(opacity=1)), unselected=dict(marker=dict(opacity=1)))
    st.plotly_chart(
        style_fig(fig3),
        use_container_width=True,
        on_select="rerun",
        selection_mode="points",
        key=REGION_CHART_KEY,
    )
