"""Applies the app's font + a transparent background to every chart so
plots read as part of the same dashboard card instead of their own
black rectangle (plotly_dark's default background doesn't match
this app's palette) — letting the surrounding bordered container's
color show through instead of painting a second, separate panel."""
from utils.theme import TEXT_MUTED

TRANSPARENT = "rgba(0,0,0,0)"


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
