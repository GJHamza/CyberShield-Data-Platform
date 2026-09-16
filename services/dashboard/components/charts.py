"""
CyberShield SOC Dashboard - Plotly Visual Analytics Components
Provides reusable, enterprise SOC dark-themed Plotly charts.
"""

from typing import Any, Dict, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# Color Palettes for SOC Dark Theme
SEVERITY_COLORS = {
    "critical": "#f85149",
    "high": "#d29922",
    "medium": "#e3b341",
    "low": "#3fb950",
    "unknown": "#8b949e",
}

RISK_LEVEL_COLORS = {
    "CRITICAL": "#f85149",
    "HIGH": "#d29922",
    "MEDIUM": "#e3b341",
    "LOW": "#3fb950",
    "UNKNOWN": "#8b949e",
}


def _apply_dark_theme(fig: go.Figure, title: str) -> go.Figure:
    """Apply consistent SOC dark theme formatting to a Plotly figure."""
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=14, color="#f0f6fc", family="system-ui, sans-serif"),
            x=0.02,
            y=0.96,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#c9d1d9", family="system-ui, sans-serif", size=12),
        margin=dict(t=45, b=25, l=25, r=25),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color="#8b949e"),
        ),
    )
    return fig


def render_severity_chart(data: Optional[Dict[str, Any]]) -> None:
    """Render Donut Chart of Events by Severity."""
    if not data or "items" not in data or not data["items"]:
        st.info("Severity distribution data unavailable.")
        return

    items = data["items"]
    df = pd.DataFrame(items)
    if df.empty or "name" not in df.columns or "count" not in df.columns:
        st.info("Severity distribution data is empty.")
        return

    df["name_clean"] = df["name"].str.lower()
    df["color"] = df["name_clean"].map(lambda x: SEVERITY_COLORS.get(x, "#58a6ff"))

    fig = px.pie(
        df,
        names="name",
        values="count",
        hole=0.55,
        color="name_clean",
        color_discrete_map=SEVERITY_COLORS,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+value",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
    )
    _apply_dark_theme(fig, "Events by Severity")

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_risk_level_chart(data: Optional[Dict[str, Any]]) -> None:
    """Render Donut Chart of ML Risk Levels."""
    if not data or "items" not in data or not data["items"]:
        st.info("Risk level distribution data unavailable.")
        return

    items = data["items"]
    df = pd.DataFrame(items)
    if df.empty or "name" not in df.columns or "count" not in df.columns:
        st.info("Risk level data is empty.")
        return

    df["name_upper"] = df["name"].str.upper()

    fig = px.pie(
        df,
        names="name_upper",
        values="count",
        hole=0.55,
        color="name_upper",
        color_discrete_map=RISK_LEVEL_COLORS,
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+value",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
    )
    _apply_dark_theme(fig, "ML Risk Level Distribution")

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_event_type_chart(data: Optional[Dict[str, Any]]) -> None:
    """Render Horizontal Bar Chart of Event Types."""
    if not data or "items" not in data or not data["items"]:
        st.info("Event type distribution data unavailable.")
        return

    items = data["items"]
    df = pd.DataFrame(items)
    if df.empty or "name" not in df.columns or "count" not in df.columns:
        st.info("Event type data is empty.")
        return

    df = df.sort_values(by="count", ascending=True)

    fig = px.bar(
        df,
        x="count",
        y="name",
        orientation="h",
        text="count",
        color_discrete_sequence=["#58a6ff"],
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Count: %{x}<extra></extra>",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#21262d", title=None)
    fig.update_yaxes(showgrid=False, title=None)
    _apply_dark_theme(fig, "Event Types & Attack Vectors")

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_anomaly_chart(overview: Optional[Dict[str, Any]]) -> None:
    """Render Donut Chart comparing Normal Events vs Anomalies."""
    if not overview or "total_events" not in overview:
        st.info("Anomaly overview data unavailable.")
        return

    total_events = overview.get("total_events", 0)
    anomalies = overview.get("total_anomalies", 0)
    normal = max(0, total_events - anomalies)

    df = pd.DataFrame({
        "Category": ["Normal Events", "ML Anomalies"],
        "Count": [normal, anomalies],
    })

    fig = px.pie(
        df,
        names="Category",
        values="Count",
        hole=0.55,
        color="Category",
        color_discrete_map={
            "Normal Events": "#3fb950",
            "ML Anomalies": "#f85149",
        },
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent+value",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<extra></extra>",
    )
    _apply_dark_theme(fig, "Anomaly Detection Breakdown")

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_events_timeline(events_data: Optional[Dict[str, Any]]) -> None:
    """Render Timeline Area Chart of Security Event Volume Over Time."""
    if not events_data or "items" not in events_data or not events_data["items"]:
        st.info("Security events timeline data unavailable.")
        return

    items = events_data["items"]
    df = pd.DataFrame(items)

    if df.empty or "timestamp" not in df.columns:
        st.info("No timestamps found for timeline chart.")
        return

    # Parse timestamps safely
    df["dt"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["dt"])

    if df.empty:
        st.info("No valid timestamps remaining for timeline chart.")
        return

    # Sort timestamps
    df = df.sort_values(by="dt")

    # Aggregate by 10-minute intervals or hourly based on span
    time_span = df["dt"].max() - df["dt"].min()
    freq = "10min" if time_span.total_seconds() <= 7200 else "h"

    df["time_bucket"] = df["dt"].dt.floor(freq)
    timeline_df = df.groupby("time_bucket").size().reset_index(name="event_count")

    fig = px.area(
        timeline_df,
        x="time_bucket",
        y="event_count",
        markers=True,
        color_discrete_sequence=["#58a6ff"],
    )
    fig.update_traces(
        fillcolor="rgba(88, 166, 255, 0.15)",
        hovertemplate="<b>Time:</b> %{x|%Y-%m-%d %H:%M}<br><b>Events:</b> %{y}<extra></extra>",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#21262d", title=None)
    fig.update_yaxes(showgrid=True, gridcolor="#21262d", title=None)
    _apply_dark_theme(fig, "Security Event Velocity (Timeline)")

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
