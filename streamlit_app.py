import streamlit as st
import rule_lookup
import general_qa

st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="wide")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition")

rule_lookup.render_rule_section()
st.markdown("---")
general_qa.render_general_section()
