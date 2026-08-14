import plotly.express as px
import streamlit as st

from utils.charts import style_fig
from utils.data_loader import load_shipments
from utils.theme import apply_theme, page_title

apply_theme()

PLOTLY_TEMPLATE = "plotly_dark"
ACCENT = "#5b8def"

page_title("📈", "Analytics", "Carrier performance, delay causes, and shipping cost trends.")

df = load_shipments()
delivered = df[df["is_delivered"]]

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
            color_discrete_sequence=["#22d3ee"],
        )
        fig2.update_layout(xaxis=dict(title="Avg days"), yaxis=dict(title=""))
        st.plotly_chart(style_fig(fig2), use_container_width=True)

st.divider()

left2, right2 = st.columns(2)

with left2:
    with st.container(border=True):
        st.subheader("Delay reasons")
        delays = df[df["delay_reason"] != ""]["delay_reason"].value_counts().reset_index()
        delays.columns = ["reason", "count"]
        fig3 = px.bar(
            delays.sort_values("count"),
            x="count",
            y="reason",
            orientation="h",
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=["#f59e0b"],
        )
        st.plotly_chart(style_fig(fig3), use_container_width=True)

with right2:
    with st.container(border=True):
        st.subheader("Shipping cost vs. weight")
        sample = df.sample(min(800, len(df)), random_state=1)
        fig4 = px.scatter(
            sample,
            x="weight_kg",
            y="shipping_cost",
            color="carrier",
            template=PLOTLY_TEMPLATE,
            opacity=0.7,
        )
        st.plotly_chart(style_fig(fig4), use_container_width=True)

with st.container(border=True):
    st.subheader("Monthly shipping cost trend")
    monthly_cost = df.groupby("order_month")["shipping_cost"].sum().reset_index()
    fig5 = px.area(monthly_cost, x="order_month", y="shipping_cost", template=PLOTLY_TEMPLATE)
    fig5.update_traces(line_color=ACCENT, fillcolor="rgba(91,141,239,0.25)")
    st.plotly_chart(style_fig(fig5), use_container_width=True)
