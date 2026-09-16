"""
CyberShield SOC Dashboard - Alert Center & Security Events Components
Renders alert tables, security events dataframes, event detail inspector, and pagination.
"""

from typing import Any, Dict, Optional
import pandas as pd
import streamlit as st


def render_alert_center(alerts_data: Optional[Dict[str, Any]]) -> None:
    """
    Render 🚨 ALERT CENTER table prioritizing security-relevant events.

    Args:
        alerts_data (dict): Response from GET /api/v1/alerts
    """
    if not alerts_data or "items" not in alerts_data or not alerts_data["items"]:
        st.info("No security alerts found matching the specified criteria.")
        return

    items = alerts_data["items"]
    rows = []
    for item in items:
        is_anomaly = item.get("is_anomaly", False)
        rows.append({
            "Event ID": item.get("event_id", "N/A"),
            "Event Type": item.get("event_type", "unknown"),
            "Severity": str(item.get("severity", "unknown")).upper(),
            "Source IP": item.get("source_ip", "N/A"),
            "Destination IP": item.get("destination_ip", "N/A"),
            "Protocol": item.get("protocol", "N/A"),
            "Risk Level": str(item.get("risk_level", "LOW")).upper(),
            "Risk Score": f"{float(item.get('risk_score', 0.0)):.1f}",
            "Anomaly": "YES" if is_anomaly else "NO",
            "Timestamp": str(item.get("timestamp", ""))[:19].replace("T", " "),
        })

    df = pd.DataFrame(rows)

    # Use Streamlit dataframe with column configuration
    st.dataframe(
        df,
        column_config={
            "Event ID": st.column_config.TextColumn("Event ID", width="medium"),
            "Risk Level": st.column_config.TextColumn("Risk Level", width="small"),
            "Risk Score": st.column_config.TextColumn("Risk Score", width="small"),
            "Anomaly": st.column_config.TextColumn("Anomaly", width="small"),
            "Severity": st.column_config.TextColumn("Severity", width="small"),
        },
        hide_index=True,
        use_container_width=True,
    )


def render_security_events_table(events_data: Optional[Dict[str, Any]]) -> None:
    """
    Render SECURITY EVENTS table.

    Args:
        events_data (dict): Response from GET /api/v1/events
    """
    if not events_data or "items" not in events_data or not events_data["items"]:
        st.info("No security events found matching the specified filters.")
        return

    items = events_data["items"]
    rows = []
    for item in items:
        rows.append({
            "Event ID": item.get("event_id", "N/A"),
            "Event Type": item.get("event_type", "unknown"),
            "Timestamp": str(item.get("timestamp", ""))[:19].replace("T", " "),
            "Source IP": item.get("source_ip", "N/A"),
            "Destination IP": item.get("destination_ip", "N/A"),
            "Protocol": item.get("protocol", "N/A"),
            "Severity": str(item.get("severity", "unknown")).upper(),
        })

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        column_config={
            "Event ID": st.column_config.TextColumn("Event ID", width="medium"),
            "Severity": st.column_config.TextColumn("Severity", width="small"),
            "Protocol": st.column_config.TextColumn("Protocol", width="small"),
        },
        hide_index=True,
        use_container_width=True,
    )


def render_event_details(event_detail: Optional[Dict[str, Any]]) -> None:
    """
    Render Deep Event Inspector displaying metadata and ML predictions.

    Args:
        event_detail (dict): Response from GET /api/v1/events/{event_id}
    """
    if not event_detail or "event_id" not in event_detail:
        st.warning("Unable to load details for the selected event.")
        return

    event_id = event_detail.get("event_id")
    event_type = event_detail.get("event_type", "N/A")
    severity = str(event_detail.get("severity", "N/A")).upper()
    timestamp = str(event_detail.get("timestamp", "N/A"))[:19].replace("T", " ")
    source_ip = event_detail.get("source_ip", "N/A")
    destination_ip = event_detail.get("destination_ip", "N/A")
    protocol = event_detail.get("protocol", "N/A")
    src_port = event_detail.get("source_port", "N/A")
    dst_port = event_detail.get("destination_port", "N/A")

    ml_result = event_detail.get("ml_result")

    st.markdown(
        f"""
        <div class="event-detail-card">
            <div class="detail-header">
                <h3>🔍 INSPECTOR: {event_id}</h3>
                <span class="badge badge-version">{severity} SEVERITY</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📋 EVENT INFORMATION")
        info_df = pd.DataFrame([
            {"Property": "Event ID", "Value": str(event_id)},
            {"Property": "Event Type", "Value": str(event_type)},
            {"Property": "Timestamp", "Value": str(timestamp)},
            {"Property": "Severity", "Value": str(severity)},
            {"Property": "Source IP:Port", "Value": f"{source_ip}:{src_port}"},
            {"Property": "Destination IP:Port", "Value": f"{destination_ip}:{dst_port}"},
            {"Property": "Protocol", "Value": str(protocol)},
        ])
        st.table(info_df.set_index("Property"))

    with col2:
        st.markdown("#### 🤖 MACHINE LEARNING ANALYSIS")
        if ml_result and isinstance(ml_result, dict):
            risk_score = ml_result.get("risk_score", 0.0)
            risk_level = ml_result.get("risk_level", "N/A")
            anomaly_score = ml_result.get("anomaly_score", 0.0)
            is_anomaly = ml_result.get("is_anomaly", False)
            model_version = ml_result.get("model_version", "N/A")
            processed_at = str(ml_result.get("processed_at", "N/A"))[:19].replace("T", " ")

            ml_df = pd.DataFrame([
                {"Metric": "Risk Score", "Value": f"{risk_score:.1f} / 100"},
                {"Metric": "Risk Level", "Value": str(risk_level)},
                {"Metric": "Anomaly Score", "Value": f"{anomaly_score:.4f}"},
                {"Metric": "Is Anomaly?", "Value": "YES (Statistical Anomaly)" if is_anomaly else "NO (Normal Pattern)"},
                {"Metric": "Model Version", "Value": str(model_version)},
                {"Metric": "Processed At", "Value": str(processed_at)},
            ])
            st.table(ml_df.set_index("Metric"))
        else:
            st.info("ML analysis not available for this event.")


def render_pagination(current_page: int, total_pages: int, key_prefix: str) -> int:
    """
    Render clean pagination controls: [◄ Prev] Page X of Y [Next ►].

    Returns:
        int: Updated page number
    """
    total_pages = max(1, total_pages)
    new_page = current_page

    col_left, col_mid, col_right = st.columns([1, 2, 1])

    with col_left:
        if st.button("◄ Previous", key=f"{key_prefix}_prev", disabled=(current_page <= 1)):
            new_page = max(1, current_page - 1)

    with col_mid:
        st.markdown(
            f"<div style='text-align: center; padding-top: 5px; color: #8b949e;'>"
            f"Page <strong>{current_page}</strong> of <strong>{total_pages}</strong>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with col_right:
        if st.button("Next ►", key=f"{key_prefix}_next", disabled=(current_page >= total_pages)):
            new_page = min(total_pages, current_page + 1)

    return new_page
