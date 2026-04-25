"""
ui/export.py
────────────
JSON/CSV export utilities.
"""

import json
import csv
import io
import streamlit as st
from typing import Dict, Any


def render_export_buttons(analysis: Dict[str, Any], protein_name: str):
    """Render download buttons for JSON and CSV export."""
    if not analysis:
        return

    safe_name = (protein_name or "protein").strip().replace(" ", "_").replace("/", "_")

    col1, col2 = st.columns(2)

    with col1:
        # JSON export
        json_data = json.dumps(
            {
                "protein_query": protein_name,
                "analysis": analysis,
            },
            indent=2,
            default=str,
        )
        st.download_button(
            "📥 Download JSON Report",
            data=json_data,
            file_name=f"{safe_name}_protscrape_report.json",
            mime="application/json",
            key="download_json",
        )

    with col2:
        # CSV export
        extracted = analysis.get("extracted_fields", {})
        attribution = analysis.get("source_attribution", {})

        if extracted:
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["Field", "Value", "Source"])
            for field, value in extracted.items():
                source = attribution.get(field, "")
                writer.writerow([field, value or "", source])

            st.download_button(
                "📥 Download CSV Fields",
                data=output.getvalue(),
                file_name=f"{safe_name}_protscrape_fields.csv",
                mime="text/csv",
                key="download_csv",
            )
