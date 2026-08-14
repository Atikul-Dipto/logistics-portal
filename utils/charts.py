"""Applies the app's single surface color + font to every chart so
plots read as part of the same dashboard instead of their own
black rectangle (plotly_dark's default background doesn't match
this app's palette)."""
from utils.theme import SURFACE, TEXT_MUTED


def style_fig(fig):
    fig.update_layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family="Plus Jakarta Sans, sans-serif", color="#e5e7eb"),
        legend=dict(font=dict(color="#e5e7eb")),
        margin=dict(t=16, b=16, l=8, r=8),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.12)", color=TEXT_MUTED)
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.08)", zerolinecolor="rgba(255,255,255,0.12)", color=TEXT_MUTED)
    return fig
