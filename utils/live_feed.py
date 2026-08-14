"""A simulated real-time activity feed. There's no live company data
source behind this portfolio project, so "real-time" here means a
genuinely auto-refreshing view (via st.fragment's run_every, no
external service or extra cost) fed by freshly-generated synthetic
events, rather than a static illusion.
"""
import random
from datetime import datetime

import streamlit as st

from utils.data_loader import load_last_mile

EVENT_TEMPLATES = [
    ("📦", "Pickup completed"),
    ("🚚", "In transit"),
    ("✅", "Delivered"),
    ("⚠️", "Delivery delayed"),
    ("🏭", "Arrived at hub"),
]


def _vocab():
    lm = load_last_mile()
    hubs = sorted(lm["destination_hub"].unique())
    zones = sorted(lm["shipping_zone"].unique())
    return hubs, zones


def _random_event(hubs, zones):
    icon, label = random.choice(EVENT_TEMPLATES)
    hub = random.choice(hubs)
    zone = random.choice(zones)
    shipment_id = f"SHP{random.randint(100000, 199999)}"
    return {
        "time": datetime.now().strftime("%H:%M:%S"),
        "icon": icon,
        "label": label,
        "detail": f"{shipment_id} · {hub} · {zone}",
    }


def render_live_feed():
    hubs, zones = _vocab()
    if "live_events" not in st.session_state:
        st.session_state.live_events = [_random_event(hubs, zones) for _ in range(5)]
        st.session_state.live_tick = 0
    _live_fragment(hubs, zones)


@st.fragment(run_every="4s")
def _live_fragment(hubs, zones):
    st.session_state.live_tick += 1
    st.session_state.live_events.insert(0, _random_event(hubs, zones))
    st.session_state.live_events = st.session_state.live_events[:8]

    with st.container(border=True):
        header_l, header_r = st.columns([1, 3])
        with header_l:
            st.markdown('<div class="live-badge"><span class="live-dot"></span>LIVE</div>', unsafe_allow_html=True)
        with header_r:
            st.caption(f"{len(st.session_state.live_events)} recent network events · auto-refreshing")

        for ev in st.session_state.live_events:
            st.markdown(
                f'<div class="live-event">'
                f'<span class="live-event__icon">{ev["icon"]}</span>'
                f'<span class="live-event__label">{ev["label"]}</span>'
                f'<span class="live-event__detail">{ev["detail"]}</span>'
                f'<span class="live-event__time">{ev["time"]}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )
