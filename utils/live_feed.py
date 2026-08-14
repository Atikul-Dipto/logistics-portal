"""A simulated real-time activity feed. There's no live company data
source behind this portfolio project, so "real-time" here means a
genuinely auto-refreshing view (via st.fragment's run_every, no
external service or extra cost) fed by real rows sampled from the
same last-mile table the rest of the app reads, rather than an
unrelated random shipment ID and a static illusion.
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
    return lm[["shipment_id", "destination_hub", "destination_region"]]


def _random_event(rows):
    icon, label = random.choice(EVENT_TEMPLATES)
    row = rows.sample(1).iloc[0]
    return {
        "time": datetime.now().strftime("%H:%M:%S"),
        "icon": icon,
        "label": label,
        "detail": f"{row['shipment_id']} · {row['destination_hub']} · {row['destination_region']}",
    }


def render_live_feed():
    rows = _vocab()
    if "live_events" not in st.session_state:
        st.session_state.live_events = [_random_event(rows) for _ in range(5)]
        st.session_state.live_tick = 0
    _live_fragment(rows)


@st.fragment(run_every="4s")
def _live_fragment(rows):
    st.session_state.live_tick += 1
    st.session_state.live_events.insert(0, _random_event(rows))
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
