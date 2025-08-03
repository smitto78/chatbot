import os
import streamlit as st
from openai import OpenAI
from agents import set_default_openai_key

import rule_lookup
import general_qa

os.environ["OPENAI_TRACING_ENABLED"] = "true"

# Setup
set_default_openai_key(st.secrets["openai"]["api_key"])
client = OpenAI(api_key=st.secrets["openai"]["api_key"])
CONFIG = {
    "RULE_PROMPT_ID": "pmpt_688eb6bb5d2c8195ae17efd5323009e0010626afbd178ad9",
    "VECTOR_STORE_ID": "vs_688ed4dbc96081919239650f07d7046f",
    "ASSISTANT_ID": "asst_AAbf5acxGSYy6NpApw2oqiZg"
}

# Page setup
st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="wide")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition")

# Session defaults
for key in ("qa_thread_id", "qa_last_prompt", "qa_last_reply", "rule_input", "rule_result"):
    st.session_state.setdefault(key, "")

# Render sections
rule_lookup.render_rule_section())
st.markdown("---")
general_qa.render_general_section()
