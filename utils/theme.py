"""Shared visual polish: a classy font pairing, a unified type scale,
an animated gradient background, and an animated/responsive filter
panel — injected once per page. Loosely modeled on searates.com's
bold-headline + pill-control language, kept in this app's existing
dark palette.

One color system, everywhere: the app background, sidebar, bordered
containers, KPI cards, dataframe grid, and chart backgrounds all
share the same two tones (BG / SURFACE) instead of each defaulting
to its own shade of near-black, which previously made every block
look like a disconnected cutout rather than part of one dashboard.
"""
import streamlit as st

BG = "#0f1115"
SURFACE = "#161a22"
SURFACE_BORDER = "rgba(255, 255, 255, 0.09)"
TEXT_MUTED = "#9aa3af"
ACCENT = "#5b8def"

_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

/* ---------- font + unified type scale ----------
   Set on the root only — relies on normal inheritance so Streamlit's
   own icon fonts (e.g. the sidebar collapse glyph) keep working. An
   earlier version forced this with !important on every div/span and
   broke those icon ligatures. */
html, body, .stApp {
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    font-size: 16px;
}

h1, h2, h3, .stApp [data-testid="stMetricValue"] {
    font-family: 'Sora', 'Plus Jakarta Sans', sans-serif !important;
    letter-spacing: -0.01em;
    color: #eef1fb !important;
}

/* Streamlit's defaults for these run noticeably smaller than body
   text (captions ~12.8px, widget labels ~14px, dataframe cells
   ~14px) which reads as an inconsistent type scale next to the
   16px body copy — bring them into one coherent scale. */
[data-testid="stCaptionContainer"], .stApp p {
    font-size: 1rem !important;
    line-height: 1.6;
}

[data-testid="stMarkdownContainer"] {
    font-size: 1rem;
}

[data-testid="stWidgetLabel"] p {
    font-size: 0.8rem !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #9aa3af !important;
}

[data-testid="stDataFrame"] {
    font-size: 0.95rem;
}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
    font-size: 0.95rem;
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

/* ---------- hero page title (searates-style bold headline) ---------- */
.hero-title {
    display: flex;
    align-items: center;
    gap: 14px;
    margin: 0 0 4px;
}

.hero-title__icon {
    font-size: 2.1rem;
    line-height: 1;
}

.hero-title__text {
    font-family: 'Sora', sans-serif;
    font-weight: 800;
    font-size: 2.5rem;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, #eef2ff 0%, #a5c4ff 55%, #5b8def 100%);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent;
}

.hero-caption {
    font-size: 1.05rem;
    color: #9aa3af;
    margin-bottom: 1.6rem;
}

/* ---------- one surface color for every card/container ----------
   Bordered containers, KPI cards (see animated_metric.py), the
   sidebar, the dataframe grid (via config.toml secondaryBackgroundColor)
   and chart backgrounds (see charts.py) all share this single tone
   instead of five different near-black shades. */
[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: #161a22 !important;
    border-color: rgba(255, 255, 255, 0.09) !important;
}

[data-testid="stMetric"] {
    transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1);
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    transition: transform 0.25s cubic-bezier(0.22, 1, 0.36, 1), box-shadow 0.25s ease,
        border-color 0.25s ease;
}

div[data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stMetric"]):hover {
    transform: translateY(-4px);
    box-shadow: 0 18px 34px -20px rgba(91, 141, 239, 0.5);
    border-color: rgba(91, 141, 239, 0.5) !important;
}

[data-testid="stDataFrame"] {
    background: #161a22;
    border-radius: 10px;
    overflow: hidden;
}

/* ---------- animated, pill-styled filter panel ---------- */
/* No transform/animation on the sidebar element itself — Streamlit
   uses transform on this same element to show/hide it on narrow
   viewports, and an earlier version's entrance animation fought
   with that, leaving the sidebar stuck at a sliver width on mobile.
   The motion lives on the inner content instead (see below). */
[data-testid="stSidebar"] {
    background: #161a22;
    border-right: 1px solid rgba(255, 255, 255, 0.07);
}

@keyframes fadeInLeft {
    from { opacity: 0; transform: translateX(-12px); }
    to { opacity: 1; transform: translateX(0); }
}

/* stagger each filter control in on load */
[data-testid="stSidebarUserContent"] > div {
    animation: fadeInLeft 0.45s cubic-bezier(0.22, 1, 0.36, 1) both;
}

[data-testid="stSidebarUserContent"] > div:nth-child(1) { animation-delay: 0.03s; }
[data-testid="stSidebarUserContent"] > div:nth-child(2) { animation-delay: 0.08s; }
[data-testid="stSidebarUserContent"] > div:nth-child(3) { animation-delay: 0.13s; }
[data-testid="stSidebarUserContent"] > div:nth-child(4) { animation-delay: 0.18s; }
[data-testid="stSidebarUserContent"] > div:nth-child(5) { animation-delay: 0.23s; }
[data-testid="stSidebarUserContent"] > div:nth-child(6) { animation-delay: 0.28s; }
[data-testid="stSidebarUserContent"] > div:nth-child(7) { animation-delay: 0.33s; }
[data-testid="stSidebarUserContent"] > div:nth-child(8) { animation-delay: 0.38s; }

/* pill-shaped controls with a focus/hover glow, echoing the rounded
   unified search bar on searates.com. Streamlit mixes React Aria
   (multiselect, text input) and BaseWeb (date input) components, so
   both sets of testids/attrs are targeted. */
[data-testid="stSidebar"] [data-testid="stMultiSelectTagsContainer"],
[data-testid="stSidebar"] [data-testid="stTextInputRootElement"],
[data-testid="stSidebar"] [data-baseweb="input"] > div {
    border-radius: 999px !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.15s ease;
}

[data-testid="stSidebar"] [data-testid="stMultiSelectTagsContainer"]:hover,
[data-testid="stSidebar"] [data-testid="stTextInputRootElement"]:hover,
[data-testid="stSidebar"] [data-baseweb="input"] > div:hover {
    border-color: rgba(91, 141, 239, 0.55) !important;
    transform: translateY(-1px);
}

[data-testid="stSidebar"] [data-testid="stMultiSelectTagsContainer"]:focus-within,
[data-testid="stSidebar"] [data-testid="stTextInputRootElement"]:focus-within,
[data-testid="stSidebar"] [data-baseweb="input"]:focus-within > div {
    border-color: #5b8def !important;
    box-shadow: 0 0 0 3px rgba(91, 141, 239, 0.22) !important;
}

[data-testid="stSidebar"] [data-testid="stCheckbox"] label:hover {
    color: #eef1fb;
}

[data-testid="stSidebar"] hr {
    border-color: rgba(255, 255, 255, 0.08);
}

/* ---------- live activity feed ---------- */
.live-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-weight: 700;
    color: #4ade80;
    font-size: 0.85rem;
    letter-spacing: 0.05em;
}

.live-dot {
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #4ade80;
    animation: live-pulse 1.6s ease-in-out infinite;
}

@keyframes live-pulse {
    0% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.55); }
    70% { box-shadow: 0 0 0 8px rgba(74, 222, 128, 0); }
    100% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
}

.live-event {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 2px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    font-size: 0.92rem;
    animation: fadeInUp 0.4s ease both;
}

.live-event:last-child {
    border-bottom: none;
}

.live-event__icon {
    font-size: 1rem;
}

.live-event__label {
    font-weight: 600;
    color: #eef1fb;
    white-space: nowrap;
}

.live-event__detail {
    color: #9aa3af;
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
}

.live-event__time {
    color: #6b7280;
    font-size: 0.8rem;
    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}

@media (prefers-reduced-motion: reduce) {
    .live-dot {
        animation: none;
    }
}

/* ---------- responsive ---------- */
@media (max-width: 900px) {
    .hero-title__text { font-size: 1.9rem; }
    .hero-title__icon { font-size: 1.7rem; }
    .hero-caption { font-size: 0.95rem; }
    html, body, .stApp { font-size: 15px; }
}

@media (max-width: 640px) {
    .hero-title__text { font-size: 1.5rem; }
    .hero-title { gap: 10px; }
}

@media (prefers-reduced-motion: reduce) {
    .stApp,
    .main .block-container,
    [data-testid="stSidebar"],
    [data-testid="stSidebarUserContent"] > div {
        animation: none !important;
    }
}
</style>
"""


def apply_theme() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def page_title(icon: str, text: str, caption: str = "") -> None:
    """SeaRates-style bold hero headline: icon stays outside the
    gradient span so color emoji rendering isn't clipped to text."""
    st.markdown(
        f'<div class="hero-title"><span class="hero-title__icon">{icon}</span>'
        f'<span class="hero-title__text">{text}</span></div>',
        unsafe_allow_html=True,
    )
    if caption:
        st.markdown(f'<div class="hero-caption">{caption}</div>', unsafe_allow_html=True)
