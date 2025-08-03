import time
import asyncio
import streamlit as st
from openai import OpenAI
from typing import Optional
from agents import Agent, Runner
from agents.tracing import trace  # Tracing only for QA
from agents import set_default_openai_key

# Set API key for agents SDK
set_default_openai_key(st.secrets["openai"]["api_key"])

# Set API key for OpenAI SDK client
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# --- CONFIGURATION ---
CONFIG = {
    "RULE_PROMPT_ID": "pmpt_688eb6bb5d2c8195ae17efd5323009e0010626afbd178ad9",
    "VECTOR_STORE_ID": "vs_688ed4dbc96081919239650f07d7046f",
    "ASSISTANT_ID": "asst_AAbf5acxGSYy6NpApw2oqiZg"
}

client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# --- PAGE SETUP ---
st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="wide")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition")

# --- SESSION STATE DEFAULTS ---
for key in ("thread_id", "last_general_prompt", "last_general_reply", "last_rule_id"):
    st.session_state.setdefault(key, "")

# --- RULE LOOKUP FUNCTION (unchanged) ---
def ask_rule_lookup(rule_id: str) -> Optional[str]:
    try:
        response = client.responses.create(
            prompt={"id": CONFIG["RULE_PROMPT_ID"], "version": "29"},
            input=[{"role": "user", "content": f"id:{rule_id}"}],
            tools=[{"type": "file_search", "vector_store_ids": [CONFIG["VECTOR_STORE_ID"]]}],
            text={"format": {"type": "text"}},
            max_output_tokens=2048,
            store=True
        )

        for item in response.output:
            if hasattr(item, "text") and hasattr(item.text, "value"):
                return item.text.value.strip()
            if hasattr(item, "content"):
                for block in item.content:
                    if hasattr(block, "text"):
                        return block.text.strip()

        return f"⚠️ No written response was generated for rule `{rule_id}`."
    except Exception as exc:
        st.error(f"❌ Rule lookup failed: {exc}")
        return None

# --- GENERAL Q&A WITH TRACING ENABLED ---
async def _qa_agent_call(prompt: str, group_id: str | None = None) -> str:
    agent = Agent(name="Rules QA Assistant", instructions="Answer NFHS football rules questions.")
    # Use synchronous context manager
    with trace(workflow_name="NFHS_QA", group_id=group_id or None):
        result = await Runner.run(agent, prompt)
    return result.final_output

def ask_general(prompt: str) -> str | None:
    try:
        settings.api_key = st.secrets["openai"]["api_key"]
        group_id = st.session_state.thread_id or "default-thread"
        return asyncio.run(_qa_agent_call(prompt, group_id))
    except Exception as e:
        st.error(f"❌ QA lookup failed: {e}")
        return None

# --- UI RENDER FUNCTIONS ---
def render_rule_section() -> None:
    st.markdown("## 🔍 Look Up a Rule by ID")
    rule_input = st.text_input("Enter Rule ID (e.g., 3-4-3d):", key="rule_input")
    look_up_clicked = st.button("Look Up", key="rule_button")

    if look_up_clicked:
        if rule_input.strip():
            result = ask_rule_lookup(rule_input.strip())
            st.markdown("### 📘 Rule Lookup Result")
            st.markdown(result or f"⚠️ No result returned for rule `{rule_input}`.")
        else:
            st.warning("Please enter a rule ID to look up.")

def render_general_section() -> None:
    st.markdown("## 💬 Ask a Question About Rules or Scenarios")
    prompt = st.text_area("Enter a question or test-style scenario:",
                          placeholder="e.g., Can Team A recover their own punt after a muff?",
                          key="general_prompt")
    if st.button("Ask", key="ask_button"):
        st.session_state.last_general_prompt = prompt.strip()

    if st.session_state.last_general_prompt:
        reply = ask_general(st.session_state.last_general_prompt)
        st.session_state.last_general_reply = reply or ""
        st.markdown("### 🧠 Assistant Reply")
        st.markdown(reply or "⚠️ No response received.")

def main() -> None:
    render_general_section()
    st.markdown("---")
    render_rule_section()

if __name__ == "__main__":
    main()
