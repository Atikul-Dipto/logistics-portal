import plotly.express as px
import streamlit as st

from utils.animated_metric import animated_kpi_row
from utils.charts import style_fig
from utils.data_loader import compact_parts, load_inventory
from utils.theme import apply_theme, page_title

apply_theme()

PLOTLY_TEMPLATE = "plotly_dark"
ACCENT = "#5b8def"

page_title("🏬", "Inventory", "Stock levels by warehouse and SKU, with low-stock alerts.")

df = load_inventory()

st.sidebar.header("Filters")
warehouse = st.sidebar.multiselect("🏭 Warehouse", sorted(df["warehouse"].unique()))
category = st.sidebar.multiselect("🏷️ Category", sorted(df["category"].unique()))
low_stock_only = st.sidebar.checkbox("⚠️ Low stock only")

filtered = df.copy()
if warehouse:
    filtered = filtered[filtered["warehouse"].isin(warehouse)]
if category:
    filtered = filtered[filtered["category"].isin(category)]
if low_stock_only:
    filtered = filtered[filtered["low_stock"]]

stock_amount, stock_suffix = compact_parts(filtered["stock_value"].sum())
animated_kpi_row(
    [
        {"label": "Total units on hand", "value": int(filtered["on_hand"].sum())},
        {"label": "Total stock value", "value": stock_amount, "prefix": "BDT ", "suffix": stock_suffix},
        {"label": "Low-stock SKUs", "value": int(filtered["low_stock"].sum())},
    ]
)

st.divider()

left, right = st.columns([1, 1.2])

with left:
    with st.container(border=True):
        st.subheader("Stock value by warehouse")
        by_wh = filtered.groupby("warehouse")["stock_value"].sum().sort_values(ascending=False).reset_index()
        fig = px.bar(by_wh, x="warehouse", y="stock_value", template=PLOTLY_TEMPLATE, color_discrete_sequence=[ACCENT])
        st.plotly_chart(style_fig(fig), use_container_width=True)

with right:
    with st.container(border=True):
        st.subheader("Stock value by category")
        by_cat = filtered.groupby("category")["stock_value"].sum().sort_values(ascending=False).reset_index()
        fig2 = px.pie(
            by_cat,
            names="category",
            values="stock_value",
            hole=0.5,
            template=PLOTLY_TEMPLATE,
            color_discrete_sequence=["#5b8def", "#22d3ee", "#7c3aed", "#f59e0b", "#ef4444"],
        )
        st.plotly_chart(style_fig(fig2), use_container_width=True)

with st.container(border=True):
    st.subheader("Low-stock alerts")
    low = filtered[filtered["low_stock"]].sort_values("on_hand")
    if low.empty:
        st.success("No SKUs below reorder point for the current filters.")
    else:
        st.dataframe(
            low[["warehouse", "sku", "product", "category", "on_hand", "reorder_point", "stock_value"]],
            use_container_width=True,
            hide_index=True,
        )
