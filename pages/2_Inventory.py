import plotly.express as px
import streamlit as st

from utils.data_loader import compact_number, load_inventory

st.set_page_config(page_title="Logistics Portal · Inventory", page_icon="🏬", layout="wide")

PLOTLY_TEMPLATE = "plotly_dark"
ACCENT = "#5b8def"

st.title("🏬 Inventory")
st.caption("Stock levels by warehouse and SKU, with low-stock alerts.")

df = load_inventory()

st.sidebar.header("Filters")
warehouse = st.sidebar.multiselect("Warehouse", sorted(df["warehouse"].unique()))
category = st.sidebar.multiselect("Category", sorted(df["category"].unique()))
low_stock_only = st.sidebar.checkbox("Low stock only")

filtered = df.copy()
if warehouse:
    filtered = filtered[filtered["warehouse"].isin(warehouse)]
if category:
    filtered = filtered[filtered["category"].isin(category)]
if low_stock_only:
    filtered = filtered[filtered["low_stock"]]

c1, c2, c3 = st.columns(3)
with c1:
    with st.container(border=True):
        st.metric("Total units on hand", f"{filtered['on_hand'].sum():,}")
with c2:
    with st.container(border=True):
        st.metric("Total stock value", f"BDT {compact_number(filtered['stock_value'].sum())}")
with c3:
    with st.container(border=True):
        st.metric("Low-stock SKUs", f"{filtered['low_stock'].sum():,}")

st.divider()

left, right = st.columns([1, 1.2])

with left:
    st.subheader("Stock value by warehouse")
    by_wh = filtered.groupby("warehouse")["stock_value"].sum().sort_values(ascending=False).reset_index()
    fig = px.bar(by_wh, x="warehouse", y="stock_value", template=PLOTLY_TEMPLATE, color_discrete_sequence=[ACCENT])
    fig.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

with right:
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
    fig2.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig2, use_container_width=True)

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
