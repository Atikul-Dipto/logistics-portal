import plotly.express as px
import streamlit as st

from utils.animated_metric import animated_kpi_row
from utils.charts import CHART_COLORS, style_fig
from utils.data_loader import load_first_mile, load_last_mile
from utils.theme import apply_theme, page_title

apply_theme()

page_title(
    "🏆",
    "Hub Scorecard",
    "First-mile pickups and last-mile deliveries combined for the same 10-hub network — the \"which hub needs attention\" view.",
)

fm = load_first_mile()
lm = load_last_mile()

fm_stats = (
    fm[fm["pickup_status"].isin(["Completed", "Failed"])]
    .groupby("origin_hub")["pickup_duration_hours"]
    .agg(first_mile_volume="count", first_mile_avg_hours="mean")
    .reset_index()
    .rename(columns={"origin_hub": "hub"})
)
lm_stats = (
    lm.groupby("destination_hub")["pending_to_delivered_hours"]
    .agg(last_mile_volume="count", last_mile_avg_hours="mean")
    .reset_index()
    .rename(columns={"destination_hub": "hub"})
)

scorecard = fm_stats.merge(lm_stats, on="hub", how="outer").fillna(0)
total_volume = scorecard["first_mile_volume"] + scorecard["last_mile_volume"]
scorecard["overall_avg_hours"] = (
    scorecard["first_mile_avg_hours"] * scorecard["first_mile_volume"]
    + scorecard["last_mile_avg_hours"] * scorecard["last_mile_volume"]
) / total_volume.replace(0, 1)
scorecard = scorecard.sort_values("overall_avg_hours").reset_index(drop=True)
scorecard.insert(0, "Rank", range(1, len(scorecard) + 1))

animated_kpi_row(
    [
        {"label": "Hubs Tracked", "value": len(scorecard)},
        {"label": "Network Avg Time", "value": round(scorecard["overall_avg_hours"].mean(), 1), "decimals": 1, "suffix": " hrs"},
        {"label": "Fastest Hub", "value": round(scorecard["overall_avg_hours"].min(), 1), "decimals": 1, "suffix": " hrs"},
        {"label": "Slowest Hub", "value": round(scorecard["overall_avg_hours"].max(), 1), "decimals": 1, "suffix": " hrs"},
    ]
)

st.write("")

with st.container(border=True):
    st.subheader("Combined hub scorecard")
    st.caption("Ranked fastest to slowest by overall (volume-weighted) processing time across both legs.")
    display = scorecard.rename(
        columns={
            "hub": "Hub",
            "first_mile_volume": "First-Mile Volume",
            "first_mile_avg_hours": "First-Mile Avg (hrs)",
            "last_mile_volume": "Last-Mile Volume",
            "last_mile_avg_hours": "Last-Mile Avg (hrs)",
            "overall_avg_hours": "Overall Avg (hrs)",
        }
    ).round(2)
    st.dataframe(
        display,
        column_config={
            "Overall Avg (hrs)": st.column_config.ProgressColumn(
                "Overall Avg (hrs)", format="%.2f", min_value=0, max_value=float(display["Overall Avg (hrs)"].max())
            )
        },
        use_container_width=True,
        hide_index=True,
    )

with st.container(border=True):
    st.subheader("First-mile vs. last-mile time by hub")
    long_df = scorecard.melt(
        id_vars="hub",
        value_vars=["first_mile_avg_hours", "last_mile_avg_hours"],
        var_name="leg",
        value_name="hours",
    )
    long_df["leg"] = long_df["leg"].map({"first_mile_avg_hours": "First Mile", "last_mile_avg_hours": "Last Mile"})
    fig = px.bar(
        long_df.sort_values("hours"),
        x="hub",
        y="hours",
        color="leg",
        barmode="group",
        color_discrete_map={"First Mile": CHART_COLORS[1], "Last Mile": CHART_COLORS[0]},
    )
    fig.update_layout(xaxis=dict(title=""), yaxis=dict(title="Avg hours"), legend=dict(title=""))
    st.plotly_chart(style_fig(fig), use_container_width=True)
