import time
import streamlit as st
from openai import OpenAI
from openai_agents import trace, Runner, AgentConfig

# --- CONFIG ---
RULE_PROMPT_ID = "pmpt_688eb6bb5d2c8195ae17efd5323009e0010626afbd178ad9"
VS_VECTOR_STORE_ID = "vs_688ed4dbc96081918ceeaa63a83f4725"
ASSISTANT_ID = "asst_AAbf5acxGSYy6NpApw2oqiZg"
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

agent_config = AgentConfig(
    assistant_id=ASSISTANT_ID,
    execution_params={
        "file_search": {"vector_store_ids": [VS_VECTOR_STORE_ID]}
    }
)

# --- PAGE SETUP ---
st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="wide")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition")

# --- SESSION STATE ---
for key in ["thread_id", "last_general_prompt", "last_general_reply", "last_rule_id"]:
    st.session_state.setdefault(key, "")

# --- RULE LOOKUP FUNCTION (unchanged) ---
def ask_rule_lookup(rule_id: str) -> str | None:
    try:
        res = client.responses.create(
            prompt={"id": RULE_PROMPT_ID, "version": "29"},
            input=[{"role": "user", "content": f"id:{rule_id}"}],
            tools=[{"type": "file_search", "vector_store_ids": [VS_VECTOR_STORE_ID]}],
            text={"format": {"type": "text"}},
            max_output_tokens=2048,
            store=True
        )

        for out in res.output:
            if hasattr(out, "text") and hasattr(out.text, "value"):
                return out.text.value.strip()
            if hasattr(out, "content"):
                for block in out.content:
                    if hasattr(block, "text"):
                        return block.text.strip()

        return f"⚠️ No written response was generated for rule `{rule_id}`."

    except Exception as e:
        st.error(f"❌ Rule lookup failed: {e}")
        return None

# --- GENERAL OPEN-ENDED QUESTION FUNCTION WITH TRACING ---
def ask_general(prompt_text: str) -> str | None:
    with trace(workflow_name="General_Q&A", group_id=prompt_text):
        result = Runner.run(agent_config, user_input=prompt_text, input_type="text")
    return result.content if hasattr(result, "content") else None

# --- UI SECTIONS ---
def render_general_section():
    st.markdown("## 💬 Ask a Question About Rules or Scenarios")
    prompt = st.text_area("Enter a question or scenario:", key="general_prompt")
    if st.button("Ask General Question"):
        st.session_state.last_general_prompt = prompt.strip()

    if st.session_state.last_general_prompt:
        reply = ask_general(st.session_state.last_general_prompt)
        st.session_state.last_general_reply = reply or ""
        st.markdown("### 🧠 General Assistant Reply")
        st.markdown(reply or "⚠️ No response received.")

def render_rule_section():
    st.markdown("## 🔍 Look Up a Rule by ID")
    rule_input = st.text_input("Enter Rule ID", key="rule_input")
    if st.button("Look Up Rule"):
        st.session_state.last_rule_id = rule_input.strip()

    if st.session_state.last_rule_id:
        result = ask_rule_lookup(st.session_state.last_rule_id)
        st.markdown("### 📘 Rule Lookup Result")
        st.markdown(result or f"⚠️ No result returned for rule `{st.session_state.last_rule_id}`.")

# --- MAIN ---
render_general_section()
st.markdown("---")
render_rule_section()
