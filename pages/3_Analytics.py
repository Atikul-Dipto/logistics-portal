import plotly.express as px
import streamlit as st

from utils.animated_metric import animated_kpi_row
from utils.charts import CHART_COLORS, HEATMAP_SCALE, style_fig
from utils.data_loader import load_shipments
from utils.theme import apply_theme, page_title

apply_theme()

PLOTLY_TEMPLATE = "plotly_dark"
ACCENT = "#5b8def"
CARRIER_CHART_KEY = "analytics_carrier_chart"

page_title("📈", "Analytics", "Carrier performance, delay root causes, and shipping cost trends.")

df = load_shipments()

# ---------- horizontal filter bar ---------- #
with st.container(border=True):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        carrier_f = st.multiselect("🚚 Carrier", sorted(df["carrier"].unique()))
    with c2:
        region_f = st.multiselect("📍 Destination Region", sorted(df["destination_region"].unique()))
    with c3:
        seller_region_f = st.multiselect("🌍 Seller Region", sorted(df["seller_region"].unique()))
    with c4:
        min_date, max_date = df["order_date"].min().date(), df["order_date"].max().date()
        date_range = st.date_input("📅 Order date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)

base_filtered = df.copy()
if carrier_f:
    base_filtered = base_filtered[base_filtered["carrier"].isin(carrier_f)]
if region_f:
    base_filtered = base_filtered[base_filtered["destination_region"].isin(region_f)]
if seller_region_f:
    base_filtered = base_filtered[base_filtered["seller_region"].isin(seller_region_f)]
if isinstance(date_range, tuple) and len(date_range) == 2:
    start, end = date_range
    base_filtered = base_filtered[(base_filtered["order_date"].dt.date >= start) & (base_filtered["order_date"].dt.date <= end)]
base_delivered = base_filtered[base_filtered["is_delivered"]]

# clicking a bar in "On-time delivery rate by carrier" cross-filters
# every other chart on the page, Power-BI style
carrier_selection = st.session_state.get(CARRIER_CHART_KEY, {}).get("selection", {}).get("points", [])
clicked_carrier = carrier_selection[0]["x"] if carrier_selection else None

filtered = base_filtered.copy()
if clicked_carrier:
    filtered = filtered[filtered["carrier"] == clicked_carrier]
delivered = filtered[filtered["is_delivered"]]

if clicked_carrier:
    badge_l, badge_r = st.columns([5, 1])
    with badge_l:
        st.caption(f"🔎 Filtered to **{clicked_carrier}** (click the bar again to change it, or clear)")
    with badge_r:
        if st.button("✕ Clear", use_container_width=True):
            st.session_state.pop(CARRIER_CHART_KEY, None)
            st.rerun()

# ---------- headline KPIs ---------- #
on_time_sla = delivered["on_time"].mean() * 100 if len(delivered) else 0.0
cost_per_kg = (filtered["shipping_cost"] / filtered["weight_kg"]).mean() if len(filtered) else 0.0
avg_order_value = filtered["order_value"].mean() if len(filtered) else 0.0
return_cancel_rate = filtered["status"].isin(["Returned", "Cancelled"]).mean() * 100 if len(filtered) else 0.0

animated_kpi_row(
    [
        {"label": "On-Time SLA", "value": round(on_time_sla, 1), "decimals": 1, "suffix": "%"},
        {"label": "Avg Cost / kg", "value": round(cost_per_kg, 1), "decimals": 1, "prefix": "BDT "},
        {"label": "Avg Order Value", "value": round(avg_order_value), "prefix": "BDT "},
        {"label": "Return / Cancel Rate", "value": round(return_cancel_rate, 1), "decimals": 1, "suffix": "%"},
    ]
)

st.write("")

left, right = st.columns(2)

with left:
    with st.container(border=True):
        st.subheader("On-time delivery rate by carrier")
        st.caption("Click a bar to filter the rest of the page by that carrier.")
        by_carrier = (
            base_delivered.groupby("carrier")
            .agg(shipments=("shipment_id", "count"), on_time_rate=("on_time", "mean"))
            .reset_index()
        )
        by_carrier["on_time_rate"] *= 100
        by_carrier = by_carrier.sort_values("on_time_rate", ascending=False)
        fig = px.bar(
            by_carrier,
            x="carrier",
            y="on_time_rate",
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=[ACCENT],
            text=by_carrier["on_time_rate"].round(1).astype(str) + "%",
        )
        fig.update_layout(yaxis=dict(title="On-time %", range=[0, 100]), clickmode="event+select")
        st.plotly_chart(
            style_fig(fig),
            use_container_width=True,
            on_select="rerun",
            selection_mode="points",
            key=CARRIER_CHART_KEY,
        )

with right:
    with st.container(border=True):
        st.subheader("Average delivery time by destination region")
        by_region = delivered.groupby("destination_region")["delivery_days"].mean().sort_values().reset_index()
        fig2 = px.bar(
            by_region,
            x="delivery_days",
            y="destination_region",
            orientation="h",
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=[CHART_COLORS[1]],
        )
        fig2.update_layout(xaxis=dict(title="Avg days"), yaxis=dict(title=""))
        st.plotly_chart(style_fig(fig2), use_container_width=True)

st.divider()

left2, right2 = st.columns(2)

with left2:
    with st.container(border=True):
        st.subheader("Delay root-cause Pareto")
        st.caption("Bars ranked by frequency; the line shows cumulative share — the classic 80/20 view of where delays come from.")
        delays = filtered[filtered["delay_reason"] != ""]["delay_reason"].value_counts().reset_index()
        delays.columns = ["reason", "count"]
        delays = delays.sort_values("count", ascending=False).reset_index(drop=True)
        if len(delays):
            delays["cum_pct"] = delays["count"].cumsum() / delays["count"].sum() * 100

        fig3 = px.bar(delays, x="reason", y="count", template=PLOTLY_TEMPLATE, color_discrete_sequence=[CHART_COLORS[2]])
        fig3.add_scatter(
            x=delays["reason"],
            y=delays["cum_pct"],
            mode="lines+markers",
            name="Cumulative %",
            yaxis="y2",
            line=dict(color=CHART_COLORS[1], width=3),
        )
        fig3.update_layout(
            xaxis=dict(title=""),
            yaxis=dict(title="Shipments"),
            yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 105]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(style_fig(fig3), use_container_width=True)

with right2:
    with st.container(border=True):
        st.subheader("Cost efficiency: shipping cost per kg by carrier")
        st.caption("Log scale — cost/kg is heavily right-skewed by small, light parcels. Reveals which carriers are consistent vs. prone to expensive outliers.")
        cost_df = filtered.copy()
        cost_df["cost_per_kg"] = cost_df["shipping_cost"] / cost_df["weight_kg"]
        fig4 = px.box(
            cost_df,
            x="carrier",
            y="cost_per_kg",
            template=PLOTLY_TEMPLATE,
            color="carrier",
            color_discrete_sequence=CHART_COLORS,
            points=False,
            log_y=True,
        )
        fig4.update_layout(xaxis=dict(title=""), yaxis=dict(title="BDT / kg (log)"), showlegend=False)
        st.plotly_chart(style_fig(fig4), use_container_width=True)

left3, right3 = st.columns(2)

with left3:
    with st.container(border=True):
        st.subheader("Shipping cost vs. weight")
        sample = filtered.sample(min(800, len(filtered)), random_state=1) if len(filtered) else filtered
        fig5 = px.scatter(
            sample,
            x="weight_kg",
            y="shipping_cost",
            color="carrier",
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=CHART_COLORS,
            opacity=0.7,
        )
        st.plotly_chart(style_fig(fig5), use_container_width=True)

with right3:
    with st.container(border=True):
        st.subheader("On-time rate by carrier & month")
        st.caption("Spot seasonal dips before they become a pattern.")
        heat = delivered.copy()
        heat["month"] = heat["order_date"].dt.strftime("%Y-%m")
        pivot = heat.pivot_table(index="carrier", columns="month", values="on_time", aggfunc="mean").sort_index(axis=1) * 100
        fig6 = px.imshow(
            pivot.round(1),
            color_continuous_scale=HEATMAP_SCALE,
            aspect="auto",
            text_auto=".0f",
            labels=dict(color="On-time %"),
        )
        fig6.update_layout(xaxis=dict(title=""), yaxis=dict(title=""))
        st.plotly_chart(style_fig(fig6), use_container_width=True)

with st.container(border=True):
    st.subheader("Monthly shipping cost trend")
    monthly_cost = filtered.groupby("order_month")["shipping_cost"].sum().reset_index()
    fig7 = px.area(monthly_cost, x="order_month", y="shipping_cost", template=PLOTLY_TEMPLATE)
    fig7.update_traces(line_color=ACCENT, fillcolor="rgba(91,141,239,0.25)")
    st.plotly_chart(style_fig(fig7), use_container_width=True)
