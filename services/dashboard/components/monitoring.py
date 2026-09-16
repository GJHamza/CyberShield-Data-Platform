"""
CyberShield SOC Dashboard - Monitoring Components
Provides Top Source IP Analytics, Recent Activity Summary, and Monitoring Status Panel.
"""

from typing import Any, Dict, Optional
from collections import Counter
import pandas as pd
import plotly.express as px
import streamlit as st

from services.dashboard.components.charts import _apply_dark_theme


def render_top_source_ips_chart(events_data: Optional[Dict[str, Any]]) -> None:
    """
    Render Horizontal Bar Chart of Top 5 Source IP Addresses.
    Calculates frequency from retrieved events data without database or external lookups.
    """
    if not events_data or "items" not in events_data or not events_data["items"]:
        st.info("Top Source IP analytics unavailable.")
        return

    items = events_data["items"]
    ips = [item.get("source_ip") for item in items if item.get("source_ip")]

    if not ips:
        st.info("No valid Source IP data found in events.")
        return

    counts = Counter(ips).most_common(5)
    df = pd.DataFrame(counts, columns=["source_ip", "count"])
    df = df.sort_values(by="count", ascending=True)

    fig = px.bar(
        df,
        x="count",
        y="source_ip",
        orientation="h",
        text="count",
        color_discrete_sequence=["#58a6ff"],
    )
    fig.update_traces(
        textposition="outside",
        hovertemplate="<b>IP: %{y}</b><br>Events: %{x}<extra></extra>",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#21262d", title=None)
    fig.update_yaxes(showgrid=False, title=None)
    _apply_dark_theme(fig, "Top 5 Source IP Activity")

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def render_recent_activity(events_data: Optional[Dict[str, Any]]) -> None:
    """
    Render compact Recent Security Activity summary table.
    """
    if not events_data or "items" not in events_data or not events_data["items"]:
        st.info("Recent security activity data unavailable.")
        return

    items = events_data["items"][:10]  # Max 10 recent events
    rows = []
    for item in items:
        rows.append({
            "Timestamp": str(item.get("timestamp", ""))[:19].replace("T", " "),
            "Event Type": item.get("event_type", "unknown"),
            "Severity": str(item.get("severity", "unknown")).upper(),
            "Source IP": item.get("source_ip", "N/A"),
            "Destination IP": item.get("destination_ip", "N/A"),
            "Protocol": item.get("protocol", "N/A"),
        })

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        column_config={
            "Timestamp": st.column_config.TextColumn("Timestamp", width="medium"),
            "Severity": st.column_config.TextColumn("Severity", width="small"),
            "Protocol": st.column_config.TextColumn("Protocol", width="small"),
        },
        hide_index=True,
        use_container_width=True,
    )


def render_monitoring_summary(
    health_data: Optional[Dict[str, Any]],
    overview_data: Optional[Dict[str, Any]],
    last_updated: str,
) -> None:
    """
    Render compact operational summary panel.
    """
    api_status = "HEALTHY" if health_data and health_data.get("status") == "healthy" else "OFFLINE"
    db_status = "CONNECTED" if health_data and health_data.get("database") == "connected" else "UNKNOWN"

    total_events = overview_data.get("total_events", 0) if overview_data else 0
    total_anomalies = overview_data.get("total_anomalies", 0) if overview_data else 0
    avg_risk = overview_data.get("average_risk_score", 0.0) if overview_data else 0.0

    st.markdown(
        f"""
        <div class="monitoring-summary-box">
            <div class="summary-item">
                <span class="summary-label">API STATUS</span>
                <span class="summary-val">{api_status}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">DATABASE</span>
                <span class="summary-val">{db_status}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">TOTAL EVENTS</span>
                <span class="summary-val">{total_events:,}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">ANOMALIES</span>
                <span class="summary-val">{total_anomalies:,}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">AVG RISK</span>
                <span class="summary-val">{avg_risk:.1f}</span>
            </div>
            <div class="summary-item">
                <span class="summary-label">LAST UPDATE</span>
                <span class="summary-val">{last_updated}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
