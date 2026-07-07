# src/visualizer.py
# ------------------
# Builds interactive Plotly log track charts with QC flag overlays.

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# Colour for each issue type
ISSUE_COLORS = {
    "missing_value":   "red",
    "depth_gap":       "purple",
    "flat_line":       "red",
    "spike":           "blue",
    "range_violation": "darkred",
}

# Label for each issue type — shown in legend
ISSUE_LABELS = {
    "missing_value":   "Missing Value",
    "depth_gap":       "Depth Gap",
    "flat_line":       "Flat Line (Stuck Sensor)",
    "spike":           "Spike",
    "range_violation": "Range Violation",
}


def plot_log_tracks(df, issues_df=None, depth_col="DEPT", title="Well Log QC"):
    """
    Build an interactive multi-track log plot.

    Args:
        df: pandas DataFrame with well log data
        issues_df: DataFrame of QC issues from run_all_checks()
        depth_col: name of the depth column
        title: chart title

    Returns:
        fig: Plotly figure object
    """
    curves = [c for c in df.columns if c != depth_col]
    n_curves = len(curves)
    depth = df[depth_col]

    fig = make_subplots(
        rows=1,
        cols=n_curves,
        shared_yaxes=True,
        subplot_titles=curves,
        horizontal_spacing=0.02
    )

    for i, curve in enumerate(curves, start=1):
        fig.add_trace(
            go.Scatter(
                x=df[curve],
                y=depth,
                mode="lines",
                name=curve,
                line=dict(width=1.5),
                showlegend=False,
                hovertemplate=(
                    f"<b>{curve}</b><br>"
                    "Value: %{x:.3f}<br>"
                    "Depth: %{y:.2f}m<br>"
                    "<extra></extra>"
                )
            ),
            row=1, col=i
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=16)),
        height=700,
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    fig.update_yaxes(
        autorange="reversed",
        title_text="Depth (m)",
        col=1
    )

    return fig


def add_xaxis_style(fig, curves):
    """Apply x-axis styling to all tracks."""
    for i, curve in enumerate(curves, start=1):
        fig.update_xaxes(
            tickangle=45,
            tickfont=dict(size=8),
            nticks=3,
            col=i
        )
    return fig


def add_grid(fig, curves):
    """Add light grey grid lines to all tracks."""
    for i, curve in enumerate(curves, start=1):
        fig.update_xaxes(
            showgrid=True,
            gridcolor="lightgrey",
            gridwidth=0.5,
            col=i
        )
    fig.update_yaxes(
        showgrid=True,
        gridcolor="lightgrey",
        gridwidth=0.5,
    )
    return fig


def add_qc_flags(fig, df, issues_df, curves, depth_col="DEPT"):
    """
    Add QC flag overlays to the log tracks.
    Spikes get coloured rectangles.
    Flat lines get bold dashed red lines.
    """
    if issues_df is None or len(issues_df) == 0:
        return fig

    for i, curve in enumerate(curves, start=1):
        curve_issues = issues_df[issues_df["curve"] == curve]

        for _, issue in curve_issues.iterrows():
            color = ISSUE_COLORS.get(issue["issue_type"], "gray")

            if issue["issue_type"] == "flat_line":
                # Bold dashed red line for flat/stuck sensor
                fig.add_trace(
                    go.Scatter(
                        x=[df[curve].mean(), df[curve].mean()],
                        y=[issue["depth_start"], issue["depth_end"]],
                        mode="lines",
                        line=dict(color="red", width=3, dash="dash"),
                        name="Flat Line (Stuck Sensor)",
                        showlegend=False,
                        hovertemplate=(
                            "<b>FLAT LINE</b><br>"
                            f"Curve: {curve}<br>"
                            f"Depth: {issue['depth_start']:.2f} - "
                            f"{issue['depth_end']:.2f}m<br>"
                            f"Count: {issue['count']} samples<br>"
                            "<extra></extra>"
                        )
                    ),
                    row=1, col=i
                )
                # Label at top of flat zone
                fig.add_annotation(
                    x=df[curve].mean(),
                    y=issue["depth_start"] + 0.5,
                    xref=f"x{i}",
                    yref="y",
                    text="FLAT LINE",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor="red",
                    font=dict(size=9, color="red"),
                    bgcolor="white",
                    bordercolor="red",
                    borderwidth=1
                )

            else:
                # Coloured rectangle for spikes and other issues
                fig.add_shape(
                    type="rect",
                    xref=f"x{i}",
                    yref="y",
                    x0=df[curve].min(),
                    x1=df[curve].max(),
                    y0=issue["depth_start"],
                    y1=issue["depth_end"] + 0.1,
                    fillcolor=color,
                    opacity=0.35,
                    line_width=0,
                    layer="below"
                )
                # Label on the flag
                fig.add_annotation(
                    x=df[curve].mean(),
                    y=(issue["depth_start"] + issue["depth_end"]) / 2,
                    xref=f"x{i}",
                    yref="y",
                    text=issue["issue_type"].replace("_", " "),
                    showarrow=False,
                    font=dict(size=9, color=color),
                    bgcolor="white",
                    bordercolor=color,
                    borderwidth=1,
                    opacity=0.9
                )

    return fig


def add_legend(fig):
    """Add a colour legend explaining QC issue types."""
    # Add invisible dummy traces just for legend entries
    legend_items = [
        ("Spike", "blue", "square"),
        ("Flat Line (Stuck Sensor)", "red", "line"),
    ]

    for label, color, symbol in legend_items:
        if symbol == "line":
            fig.add_trace(
                go.Scatter(
                    x=[None], y=[None],
                    mode="lines",
                    line=dict(color=color, width=3, dash="dash"),
                    name=label,
                    showlegend=True
                )
            )
        else:
            fig.add_trace(
                go.Scatter(
                    x=[None], y=[None],
                    mode="markers",
                    marker=dict(
                        symbol="square",
                        color=color,
                        size=12,
                        opacity=0.5
                    ),
                    name=label,
                    showlegend=True
                )
            )

    fig.update_layout(
        showlegend=True,
        legend=dict(
            title=dict(
                text="QC Issue Types",
                font=dict(size=11, color="black")
            ),
            orientation="h",
            yanchor="bottom",
            y=-0.20,
            xanchor="center",
            x=0.5,
            bgcolor="lightyellow",
            bordercolor="gray",
            borderwidth=1,
            font=dict(size=10)
        ),
        margin=dict(b=100)
    )
    return fig


def fix_large_xaxis(fig, df, curves, depth_col="DEPT"):
    """Format x-axis for curves with very large values."""
    for i, curve in enumerate(curves, start=1):
        max_val = df[curve].max()
        if max_val > 1000:
            fig.update_xaxes(
                tickformat=".0f",
                col=i
            )
    return fig


def plot_completeness_heatmap(df, depth_col="DEPT", null_value=-999.25):
    """
    Build a bar chart showing data completeness for each curve.

    Args:
        df: pandas DataFrame with well log data
        depth_col: name of the depth column
        null_value: null value used in the LAS file

    Returns:
        fig: Plotly figure object
    """
    curves = [c for c in df.columns if c != depth_col]
    completeness = []

    for curve in curves:
        series = df[curve].replace(null_value, np.nan)
        pct_complete = round((series.notna().sum() / len(series)) * 100, 1)
        completeness.append(pct_complete)

    colors = []
    for v in completeness:
        if v == 100:
            colors.append("green")
        elif v >= 80:
            colors.append("orange")
        else:
            colors.append("red")

    fig = go.Figure(go.Bar(
        x=curves,
        y=completeness,
        marker_color=colors,
        text=[f"{v}%" for v in completeness],
        textposition="auto"
    ))

    fig.update_layout(
        title="Data Completeness by Curve",
        xaxis_title="Curve",
        yaxis_title="% Complete",
        yaxis=dict(range=[0, 105]),
        height=400,
        plot_bgcolor="white",
        paper_bgcolor="white"
    )
    return fig
