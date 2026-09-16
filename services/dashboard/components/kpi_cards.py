"""
CyberShield SOC Dashboard - KPI Cards Component
Renders key security metrics received from API overview endpoint.
"""

from typing import Any, Dict
import streamlit as st


def render_kpi_cards(overview: Dict[str, Any]) -> None:
    """
    Render 5 SOC KPI metric cards in a 5-column layout.

    Args:
        overview (dict): Data dict from GET /api/v1/statistics/overview
    """
    # Safe dictionary access with defaults
    total_events = overview.get("total_events", 0) if overview else 0
    critical_events = overview.get("critical_events", 0) if overview else 0
    total_anomalies = overview.get("total_anomalies", 0) if overview else 0
    anomaly_rate = overview.get("anomaly_rate", 0.0) if overview else 0.0
    average_risk_score = overview.get("average_risk_score", 0.0) if overview else 0.0

    cols = st.columns(5)

    with cols[0]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-card-title">TOTAL EVENTS</div>
                <div class="kpi-card-value primary">{total_events:,}</div>
                <div class="kpi-card-sub">Security events processed</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cols[1]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-card-title">CRITICAL EVENTS</div>
                <div class="kpi-card-value critical">{critical_events:,}</div>
                <div class="kpi-card-sub">Immediate attention required</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cols[2]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-card-title">ANOMALIES DETECTED</div>
                <div class="kpi-card-value anomaly">{total_anomalies:,}</div>
                <div class="kpi-card-sub">Detected by ML</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cols[3]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-card-title">ANOMALY RATE</div>
                <div class="kpi-card-value">{anomaly_rate:.2f}%</div>
                <div class="kpi-card-sub">Of total events</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with cols[4]:
        st.markdown(
            f"""
            <div class="kpi-card">
                <div class="kpi-card-title">AVERAGE RISK</div>
                <div class="kpi-card-value">{average_risk_score:.1f}</div>
                <div class="kpi-card-sub">ML risk score (0-100)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
