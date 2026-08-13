"""Shared visual polish: a classy font pairing, an animated gradient
background, and motion/hover treatments — injected once per page.
"""
import streamlit as st

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

/* Set on the root only — relies on normal inheritance so Streamlit's
   own icon fonts (e.g. the sidebar collapse glyph) keep working. An
   earlier version forced this with !important on every div/span and
   broke those icon ligatures. */
html, body, .stApp {
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
}

h1, h2, h3, .stApp [data-testid="stMetricValue"] {
    font-family: 'Sora', 'Plus Jakarta Sans', sans-serif !important;
    letter-spacing: -0.01em;
    color: #eef1fb !important;
}

/* ---------- animated gradient background ----------
   position:fixed doesn't reliably escape Streamlit's own layout
   containers, so the motion lives in the background paint itself
   (background-attachment: fixed) instead of a floating element. */
.stApp {
    background-color: #0f1115;
    background-image:
        radial-gradient(circle at 20% 20%, rgba(91, 141, 239, 0.32), transparent 42%),
        radial-gradient(circle at 80% 75%, rgba(124, 58, 237, 0.28), transparent 42%),
        radial-gradient(circle at 55% 45%, rgba(34, 211, 238, 0.18), transparent 36%);
    background-repeat: no-repeat;
    background-size: 160% 160%;
    background-attachment: fixed;
    animation: bgdrift 28s ease-in-out infinite;
}

@keyframes bgdrift {
    0%, 100% { background-position: 0% 0%; }
    50% { background-position: 100% 55%; }
}

/* ---------- entrance motion ---------- */
.main .block-container {
    animation: fadeInUp 0.55s cubic-bezier(0.22, 1, 0.36, 1) both;
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(14px); }
    to { opacity: 1; transform: translateY(0); }
}

/* ---------- metric / bordered card motion ---------- */
[data-testid="stMetric"] {
    transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1);
}

div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stMetric"]) {
    transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.25s ease,
        border-color 0.25s ease;
}

div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stMetric"]):hover {
    transform: translateY(-4px);
    box-shadow: 0 18px 34px -20px rgba(91, 141, 239, 0.5);
    border-color: rgba(91, 141, 239, 0.5) !important;
}

/* ---------- sidebar polish ---------- */
[data-testid="stSidebar"] {
    animation: fadeInUp 0.5s ease both;
}

@media (prefers-reduced-motion: reduce) {
    .stApp,
    .main .block-container,
    [data-testid="stSidebar"] {
        animation: none !important;
    }
}
</style>
"""


def apply_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)
