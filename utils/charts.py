"""Applies the app's font + a transparent background to every chart so
plots read as part of the same dashboard card instead of their own
black rectangle (plotly_dark's default background doesn't match
this app's palette) — letting the surrounding bordered container's
color show through instead of painting a second, separate panel.

Also centralizes the app's single categorical color palette so every
multi-series chart (pies, grouped bars, scatters colored by category)
draws from the same blue/purple/cyan family instead of each page (or
Plotly's own default rainbow) picking its own set."""
from utils.theme import TEXT_MUTED

TRANSPARENT = "rgba(0,0,0,0)"

# One qualitative palette, shared by every chart in the app that
# colors by category (carrier, status, leg, etc).
CHART_COLORS = ["#5b8def", "#22d3ee", "#7c3aed", "#f59e0b", "#4ade80", "#ef4444", "#f472b6", "#64748b"]

# Continuous scale for heatmaps, built from the same accent blue.
HEATMAP_SCALE = [[0, "#161a22"], [0.5, "#3a5aa8"], [1, "#5b8def"]]


def style_fig(fig):
    fig.update_layout(
        paper_bgcolor=TRANSPARENT,
        plot_bgcolor=TRANSPARENT,
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#e5e7eb"),
        legend=dict(font=dict(color="#e5e7eb")),
        margin=dict(t=16, b=16, l=8, r=8),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.12)", color=TEXT_MUTED)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.12)", color=TEXT_MUTED)
    return fig
