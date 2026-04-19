import streamlit as st
import json
import re

from legal_engine import run_pipeline

st.set_page_config(page_title="Legal RAG Assistant", layout="wide")

# =========================
# SAFE JSON PARSER
# =========================
def safe_parse_json(text):
    try:
        return json.loads(text)
    except:
        # remove markdown ```json ```
        text = re.sub(r"```json|```", "", text)

        # extract JSON block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except:
                return None
    return None

# =========================
# HEADER
# =========================
st.title("⚖️ Legal Crime Analyzer")
st.markdown("Analyze crime scenarios and retrieve relevant legal provisions.")

# =========================
# INPUT
# =========================
query = st.text_area(
    "Enter crime scenario:",
    placeholder="Example: A person broke into a house at night and stole valuables...",
    height=150
)

# =========================
# RUN BUTTON
# =========================
if st.button("Analyze"):
    if not query.strip():
        st.warning("Please enter a scenario.")
    else:
        with st.spinner("Analyzing..."):
            result = run_pipeline(query)

        # =========================
        # PARSE OUTPUT (SAFE)
        # =========================
        result_json = safe_parse_json(result)

        if result_json is None:
            st.error("⚠️ Failed to parse response. Showing raw output.")
            st.code(result, language="json")
            st.stop()

        # =========================
        # DISPLAY CRIME TYPES
        # =========================
        st.subheader("🔍 Identified Crime Types")

        if result_json.get("crime_type"):
            for crime in result_json["crime_type"]:
                st.success(crime)
        else:
            st.warning("No crime types identified.")

        # =========================
        # DISPLAY LAWS
        # =========================
        st.subheader("📚 Applicable Laws")

        laws = result_json.get("applicable_laws", [])

        if not laws:
            st.warning("No applicable laws found.")
        else:
            for law in laws:
                with st.expander(f"{law.get('act')} - Section {law.get('section')}"):
                    
                    st.markdown("**Description:**")
                    st.write(law.get("description", ""))

                    st.markdown("**Justification:**")
                    st.info(law.get("justification", ""))

# =========================
# FOOTER
# =========================
st.markdown("---")
st.caption("Built using RAG + LLM for legal reasoning")