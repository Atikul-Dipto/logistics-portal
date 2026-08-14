import plotly.express as px
import streamlit as st

from utils.animated_metric import animated_kpi_row
from utils.charts import CHART_COLORS, HEATMAP_SCALE, style_fig
from utils.data_loader import load_shipments
from utils.theme import apply_theme, page_title

apply_theme()

PLOTLY_TEMPLATE = "plotly_dark"
ACCENT = "#5b8def"

page_title("📈", "Analytics", "Carrier performance, delay root causes, and shipping cost trends.")

df = load_shipments()
delivered = df[df["is_delivered"]]

# ---------- headline KPIs ---------- #
on_time_sla = delivered["on_time"].mean() * 100 if len(delivered) else 0.0
cost_per_kg = (df["shipping_cost"] / df["weight_kg"]).mean()
avg_order_value = df["order_value"].mean()
return_cancel_rate = df["status"].isin(["Returned", "Cancelled"]).mean() * 100

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
        by_carrier = (
            delivered.groupby("carrier")
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
        fig.update_layout(yaxis=dict(title="On-time %", range=[0, 100]))
        st.plotly_chart(style_fig(fig), use_container_width=True)

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
        delays = df[df["delay_reason"] != ""]["delay_reason"].value_counts().reset_index()
        delays.columns = ["reason", "count"]
        delays = delays.sort_values("count", ascending=False).reset_index(drop=True)
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
        cost_df = df.copy()
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
        sample = df.sample(min(800, len(df)), random_state=1)
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
    monthly_cost = df.groupby("order_month")["shipping_cost"].sum().reset_index()
    fig7 = px.area(monthly_cost, x="order_month", y="shipping_cost", template=PLOTLY_TEMPLATE)
    fig7.update_traces(line_color=ACCENT, fillcolor="rgba(91,141,239,0.25)")
    st.plotly_chart(style_fig(fig7), use_container_width=True)
