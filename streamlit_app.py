import time
import streamlit as st
from openai import OpenAI

# --- CONFIG ---
RULE_PROMPT_ID = "pmpt_688eb6bb5d2c8195ae17efd5323009e0010626afbd178ad9"
VS_VECTOR_STORE_ID = "vs_68883bb7d06881918ceeaa63a83f4725"
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# --- PAGE SETUP ---
st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="wide")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition")
st.caption("Ask a question or look up a rule. Built for players, coaches, and officials.")

# --- RULE LOOKUP FUNCTION ---
def ask_rule_lookup(rule_id: str) -> str | None:
    try:
        # Frame the input with context to align with assistant expectations
        input_text = f"What does rule {rule_id} say?"

        response = client.responses.create(
            prompt={
                "id": RULE_PROMPT_ID,
                "version": "11"
            },
            input=[{"role": "user", "content": input_text}],
            text={"format": {"type": "text"}},
            reasoning={},
            tools=[{
                "type": "file_search",
                "vector_store_ids": [VS_VECTOR_STORE_ID]
            }],
            max_output_tokens=2048,
            store=True
        )

        # Iterate through the response output to find a valid text block
        for item in response.output:
            if hasattr(item, "text") and hasattr(item.text, "value"):
                return item.text.value

        return f"⚠️ No written response was generated for rule `{rule_id}`. Ensure this rule exists in your file search."
    
    except Exception as e:
        st.error(f"❌ Rule lookup failed: {e}")
        return None


# --- RULE LOOKUP UI ---
def render_rule_section():
    st.markdown("## 🔍 Look Up a Rule by ID")
    rule_input = st.text_input("Enter Rule ID (e.g., 3-4-3d):", key="rule_input")
    if st.button("Look Up"):
        if rule_input.strip():
            result = ask_rule_lookup(rule_input.strip())
            st.markdown("### 📘 Rule Lookup Result")
            st.markdown(result or f"⚠️ No result returned for rule `{rule_input}`.")
        else:
            st.warning("Please enter a rule ID to look up.")

# --- MAIN ---
render_rule_section()
