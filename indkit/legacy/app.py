from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from ind_m1_poc.form_1571 import render_form_1571_markdown  # noqa: E402
from ind_m1_poc.loader import list_cases, load_source_case  # noqa: E402
from ind_m1_poc.orchestrator import generate_module1_package  # noqa: E402
from ind_m1_poc.paths import OUTPUTS_DIR  # noqa: E402
from ind_m1_poc.validation import render_validation_markdown  # noqa: E402


st.set_page_config(page_title="IND Module 1 POC Agent", layout="wide")

st.title("IND Module 1 POC Agent")
st.caption("Synthetic data demo. Outputs are POC drafts and are not FDA-submission-ready.")

cases = list_cases()
case_labels = {f"{case['case_id']} - {case['case_label'].split(' - ', 1)[-1]}": case for case in cases}

left, right = st.columns([1, 2])

with left:
    selected_label = st.selectbox("Demo Case", list(case_labels.keys()))
    selected_case = case_labels[selected_label]
    use_llm = st.toggle("Use LLM for Cover Letter when configured", value=True)
    generate = st.button("Generate Module 1 Package", type="primary", use_container_width=True)

    source_case = load_source_case(selected_case["case_id"])
    st.subheader("Case Snapshot")
    st.write(f"Scenario: `{source_case['scenario_type']}`")
    st.write(f"Source records: `{len(source_case['source_records'])}`")
    with st.expander("Agent-visible source data"):
        st.json(source_case)

package = None
if generate:
    package = generate_module1_package(selected_case["case_id"], use_llm=use_llm)
    st.session_state["last_package"] = package
elif st.session_state.get("last_package", {}).get("case_id") == selected_case["case_id"]:
    package = st.session_state["last_package"]

with right:
    if not package:
        st.info("Select a case and generate the package.")
    else:
        summary = package["validation"]["summary"]
        st.success(
            "Generated Cover Letter, FDA 1571 Field View, Module 1 TOC, and Validation artifacts."
        )
        metric_cols = st.columns(4)
        for col, status in zip(metric_cols, ["PASS", "WARNING", "MISSING", "CONFLICT"]):
            col.metric(status, summary[status])

        st.write(f"Artifacts persisted to `{OUTPUTS_DIR / package['case_id']}`")
        if package["cover_letter"]["warnings"]:
            for warning in package["cover_letter"]["warnings"]:
                st.warning(warning)

        cover_tab, form_tab, toc_tab, validation_tab, provenance_tab = st.tabs(
            ["Cover Letter", "FDA 1571", "TOC", "Validation", "Provenance"]
        )

        with cover_tab:
            st.markdown(package["cover_letter"]["text"])
            st.download_button(
                "Download Cover Letter",
                data=package["cover_letter"]["text"],
                file_name=f"{package['case_id']}_cover_letter.md",
                mime="text/markdown",
            )

        with form_tab:
            form_markdown = render_form_1571_markdown(package["form_1571"])
            st.markdown(form_markdown)
            st.download_button(
                "Download 1571 Field View",
                data=form_markdown,
                file_name=f"{package['case_id']}_form_1571.md",
                mime="text/markdown",
            )

        with toc_tab:
            st.markdown(package["toc"]["markdown"])
            st.download_button(
                "Download TOC",
                data=package["toc"]["markdown"],
                file_name=f"{package['case_id']}_module1_toc.md",
                mime="text/markdown",
            )

        with validation_tab:
            validation_markdown = render_validation_markdown(package["validation"])
            st.markdown(validation_markdown)
            st.download_button(
                "Download Validation",
                data=validation_markdown,
                file_name=f"{package['case_id']}_validation.md",
                mime="text/markdown",
            )

        with provenance_tab:
            st.json(package["canonical"]["provenance"])

