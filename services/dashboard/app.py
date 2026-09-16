"""
CyberShield Data Platform - Streamlit SOC Dashboard
Main application entry point with Auto-Refresh, Monitoring, Visual Analytics, Alert Center, and Events.
"""

from datetime import datetime, timezone
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

# Streamlit Page Configuration (MUST be the first Streamlit command)
st.set_page_config(
    page_title="CyberShield SOC",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

from services.dashboard.api_client import CyberShieldAPIClient
from services.dashboard.components.alert_tables import (
    render_alert_center,
    render_event_details,
    render_pagination,
    render_security_events_table,
)
from services.dashboard.components.charts import (
    render_anomaly_chart,
    render_event_type_chart,
    render_events_timeline,
    render_risk_level_chart,
    render_severity_chart,
)
from services.dashboard.components.kpi_cards import render_kpi_cards
from services.dashboard.components.monitoring import (
    render_monitoring_summary,
    render_recent_activity,
    render_top_source_ips_chart,
)
from services.dashboard.config import APP_NAME, APP_VERSION


def load_css() -> None:
    """Safely load custom CSS stylesheet for enterprise dark theme."""
    css_path = Path(__file__).parent / "styles" / "custom.css"
    if css_path.exists():
        try:
            with open(css_path, "r", encoding="utf-8") as f:
                st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        except Exception:
            pass


def main() -> None:
    # 1. Load Custom CSS
    load_css()

    # 2. Last Updated Timestamp (UTC)
    last_updated_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # 3. Session State Initialization
    if "alerts_page" not in st.session_state:
        st.session_state.alerts_page = 1
    if "events_page" not in st.session_state:
        st.session_state.events_page = 1

    # 4. Instantiate API Client
    client = CyberShieldAPIClient()

    # 5. Sidebar Navigation & Monitoring Controls
    st.sidebar.markdown(f"## 🛡️ {APP_NAME}")
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ SOC MONITORING")

    refresh_choice = st.sidebar.selectbox(
        "Auto-Refresh Interval",
        options=["30 seconds", "10 seconds", "60 seconds", "OFF"],
        index=0,
        key="auto_refresh_choice",
    )

    is_auto_refresh = refresh_choice != "OFF"
    monitoring_status = "ACTIVE" if is_auto_refresh else "PAUSED"
    monitoring_badge_class = "badge-active" if is_auto_refresh else "badge-paused"

    # Inject Non-Blocking Auto-Refresh Script
    if is_auto_refresh:
        interval_seconds = int(refresh_choice.split()[0])
        components.html(
            f"<script>setTimeout(function(){{ window.parent.location.reload(); }}, {interval_seconds * 1000});</script>",
            height=0,
        )

    st.sidebar.markdown("---")
    st.sidebar.markdown("📌 **SOC Overview & Analytics**")
    st.sidebar.markdown("🚨 **Alert Center**")
    st.sidebar.markdown("📋 **Security Events**")
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"""
        <div class="sidebar-footer">
            <strong>CyberShield Data Platform</strong><br>
            SOC Dashboard v{APP_VERSION}
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 6. Fetch Core Status & KPI Overview Data
    health_data, health_err = client.health()
    overview_data, overview_err = client.get_overview()

    # 7. Header Component with Dynamic Status & Monitoring Badges
    api_status = "healthy" if health_data and health_data.get("status") == "healthy" else "offline"
    db_status = "connected" if health_data and health_data.get("database") == "connected" else "unknown"

    api_badge_class = "badge-success" if api_status == "healthy" else "badge-danger"
    db_badge_class = "badge-success" if db_status == "connected" else "badge-danger"

    st.markdown(
        f"""
        <div class="soc-header">
            <div class="soc-title-section">
                <h1>🛡️ CYBERSHIELD SOC</h1>
                <p>Security Operations Center & Real-Time Monitoring</p>
            </div>
            <div class="soc-status-badges">
                <span class="badge {monitoring_badge_class}">MONITORING ● {monitoring_status}</span>
                <span class="badge {api_badge_class}">API ● {api_status.upper()}</span>
                <span class="badge {db_badge_class}">DATABASE ● {db_status.upper()}</span>
                <span class="badge badge-version">v{APP_VERSION}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Global API Connection Notification
    if health_err or overview_err:
        err_msg = overview_err or health_err or "CyberShield API is currently unavailable."
        st.error(f"⚠️ {err_msg}")

    # 8. Operational Summary Bar
    render_monitoring_summary(health_data, overview_data, last_updated_str)

    # 9. Render KPI Cards Component
    render_kpi_cards(overview_data or {})

    st.markdown("---")

    # 10. Fetch Sample Events for Dynamic Filters & Analytics
    sample_events_resp, _ = client.get_events(page=1, page_size=100)
    sample_items = sample_events_resp.get("items", []) if sample_events_resp else []

    # Dynamic Discovery of Protocols and Event Types (NO hardcoding!)
    discovered_protocols = ["All"] + sorted(list({str(item["protocol"]).strip() for item in sample_items if item.get("protocol")}))
    discovered_event_types = ["All"] + sorted(list({str(item["event_type"]).strip() for item in sample_items if item.get("event_type")}))

    # 11. Threat Intelligence & Visual Analytics Section
    st.subheader("THREAT INTELLIGENCE & VISUAL ANALYTICS")

    severity_data, _ = client.get_severity_statistics()
    risk_level_data, _ = client.get_risk_level_statistics()
    event_type_stats, _ = client.get_event_type_statistics()

    col1, col2 = st.columns(2)
    with col1:
        render_severity_chart(severity_data)
    with col2:
        render_risk_level_chart(risk_level_data)

    st.markdown("<br>", unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        render_event_type_chart(event_type_stats)
    with col4:
        render_anomaly_chart(overview_data)

    st.markdown("<br>", unsafe_allow_html=True)
    render_events_timeline(sample_events_resp)

    st.markdown("<br>", unsafe_allow_html=True)

    # 12. Top Source IPs & Recent Activity Monitoring
    col5, col6 = st.columns(2)
    with col5:
        render_top_source_ips_chart(sample_events_resp)
    with col6:
        st.markdown("#### RECENT SECURITY ACTIVITY")
        render_recent_activity(sample_events_resp)

    st.markdown("---")

    # 13. SECTION 1 — ALERT CENTER
    st.subheader("🚨 ALERT CENTER")
    st.caption("Prioritized security alerts and machine learning anomaly detections.")

    # Advanced Alert Filters Area
    alert_col1, alert_col2, alert_col3, alert_col4 = st.columns(4)

    with alert_col1:
        selected_risk = st.selectbox(
            "Risk Level",
            options=["All", "CRITICAL", "HIGH", "MEDIUM", "LOW"],
            key="filter_alert_risk",
        )

    with alert_col2:
        selected_anomaly = st.selectbox(
            "Anomaly Status",
            options=["All", "Anomalies Only", "Normal Only"],
            key="filter_alert_anomaly",
        )

    with alert_col3:
        selected_min_score = st.selectbox(
            "Minimum Risk Score",
            options=[0, 25, 50, 75, 90],
            key="filter_alert_min_score",
        )

    with alert_col4:
        selected_max_score = st.selectbox(
            "Maximum Risk Score",
            options=[100, 90, 75, 50, 25],
            key="filter_alert_max_score",
        )

    # Min/Max Risk Score Validation
    if selected_min_score > selected_max_score:
        st.warning("⚠️ Minimum risk score cannot be greater than maximum risk score.")
        alerts_response = None
    else:
        # Process Alert Filter Arguments
        filter_risk_arg = None if selected_risk == "All" else selected_risk
        filter_anomaly_arg = None
        if selected_anomaly == "Anomalies Only":
            filter_anomaly_arg = True
        elif selected_anomaly == "Normal Only":
            filter_anomaly_arg = False

        filter_min_score_arg = None if selected_min_score == 0 else float(selected_min_score)

        # Fetch Alert Data
        alerts_response, alerts_err = client.get_alerts(
            page=st.session_state.alerts_page,
            page_size=10,
            risk_level=filter_risk_arg,
            is_anomaly=filter_anomaly_arg,
            min_risk_score=filter_min_score_arg,
        )

        if alerts_err:
            st.warning("Alert Center data is temporarily unavailable.")

    if alerts_response:
        render_alert_center(alerts_response)
        total_alerts_pages = alerts_response.get("total_pages", 1) if alerts_response else 1
        new_alert_page = render_pagination(st.session_state.alerts_page, total_alerts_pages, key_prefix="alerts")
        if new_alert_page != st.session_state.alerts_page:
            st.session_state.alerts_page = new_alert_page
            st.rerun()

    st.markdown("---")

    # 14. SECTION 2 — SECURITY EVENTS TABLE
    st.subheader("📋 SECURITY EVENTS TABLE")
    st.caption("Explore, filter, and inspect raw security events processed by CyberShield.")

    # Event Filters Area (Dynamic Discovery)
    ev_col1, ev_col2, ev_col3, ev_col4, ev_col5 = st.columns(5)

    with ev_col1:
        selected_severity = st.selectbox(
            "Severity",
            options=["All", "critical", "high", "medium", "low"],
            key="filter_ev_severity",
        )
    with ev_col2:
        selected_evt_type = st.selectbox(
            "Event Type",
            options=discovered_event_types,
            key="filter_ev_type",
        )
    with ev_col3:
        selected_protocol = st.selectbox(
            "Protocol",
            options=discovered_protocols,
            key="filter_ev_protocol",
        )
    with ev_col4:
        input_source_ip = st.text_input("Source IP", placeholder="e.g. 192.168.1.50", key="filter_ev_source_ip")
    with ev_col5:
        selected_date = st.date_input("Event Date", value=None, key="filter_ev_date")

    # Process Event Filter Arguments
    ev_sev_arg = None if selected_severity == "All" else selected_severity
    ev_type_arg = None if selected_evt_type == "All" else selected_evt_type
    ev_proto_arg = None if selected_protocol == "All" else selected_protocol
    ev_ip_arg = input_source_ip.strip() if input_source_ip else None
    ev_date_arg = str(selected_date) if selected_date else None

    # Fetch Security Events Data
    events_response, events_err = client.get_events(
        page=st.session_state.events_page,
        page_size=10,
        severity=ev_sev_arg,
        event_type=ev_type_arg,
        source_ip=ev_ip_arg,
        protocol=ev_proto_arg,
        event_date=ev_date_arg,
    )

    if events_err:
        st.warning("Security Events data is temporarily unavailable.")
    else:
        render_security_events_table(events_response)
        total_events_pages = events_response.get("total_pages", 1) if events_response else 1
        new_event_page = render_pagination(st.session_state.events_page, total_events_pages, key_prefix="events")
        if new_event_page != st.session_state.events_page:
            st.session_state.events_page = new_event_page
            st.rerun()

        # 15. EVENT INSPECTOR / SELECTION
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("🔍 EVENT DETAILS INSPECTOR")

        event_items = events_response.get("items", []) if events_response else []
        event_ids_list = [item["event_id"] for item in event_items if "event_id" in item]

        if event_ids_list:
            selected_id = st.selectbox(
                "Select Event ID to inspect:",
                options=["None"] + event_ids_list,
                key="event_inspector_selectbox",
            )

            if selected_id and selected_id != "None":
                event_detail_data, detail_err = client.get_event(selected_id)
                if detail_err:
                    st.warning("Unable to load event details.")
                else:
                    render_event_details(event_detail_data)
        else:
            st.info("No events available to inspect.")


if __name__ == "__main__":
    main()
