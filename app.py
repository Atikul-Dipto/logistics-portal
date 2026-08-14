import streamlit as st

st.set_page_config(page_title="Logistics Operations Portal", page_icon="📦", layout="wide")

overview = st.Page("pages/0_Overview.py", title="Overview", icon="📦", default=True)
shipments = st.Page("pages/1_Shipments.py", title="Shipments", icon="🚚")
inventory = st.Page("pages/2_Inventory.py", title="Inventory", icon="🏬")
analytics = st.Page("pages/3_Analytics.py", title="Analytics", icon="📈")
last_mile = st.Page("pages/4_LastMile.py", title="Last Mile", icon="⏱️")
first_mile = st.Page("pages/5_FirstMile.py", title="First Mile", icon="📥")
hub_scorecard = st.Page("pages/6_HubScorecard.py", title="Hub Scorecard", icon="🏆")

pg = st.navigation(
    [overview, shipments, inventory, analytics, first_mile, last_mile, hub_scorecard]
)
pg.run()
