import streamlit as st
import asyncio
from agents import Agent, Runner
from agents.tracing import trace

async def _qa_agent_call(prompt: str, group_id: str | None = None) -> str:
    agent = Agent(
        name="Rules QA Assistant",
        instructions="Only answer questions if grounded in NFHS rules. Say 'I don't know' if unsure."
    )
    with trace(workflow_name="NFHS_QA", group_id=group_id):
        result = await Runner.run(agent, prompt)
    return result.final_output

def ask_general(prompt: str) -> str | None:
    try:
        group_id = st.session_state.qa_thread_id or "default-thread"
        return asyncio.run(_qa_agent_call(prompt, group_id))
    except Exception as e:
        st.error(f"❌ QA lookup failed: {e}")
        return None

def render_general_section():
    # Ensure only QA-related session keys are initialized here
    for key in ("qa_prompt_input", "qa_thread_id", "qa_last_prompt", "qa_last_reply"):
        st.session_state.setdefault(key, "")

    # Only clear rule lookup keys if they exist
    if st.session_state["qa_prompt_input"]:
        if "rule_lookup_input" in st.session_state:
            st.session_state["rule_lookup_input"] = ""
        if "rule_lookup_result" in st.session_state:
            st.session_state["rule_lookup_result"] = ""

    # UI
    st.markdown("## 💬 Ask a Question About Rules or Scenarios")
    prompt = st.text_area("Enter your question:", key="qa_prompt_input")

    if st.button("Ask", key="qa_button"):
        st.session_state.qa_last_prompt = prompt.strip()

    if st.session_state.qa_last_prompt:
        reply = ask_general(st.session_state.qa_last_prompt)
        st.session_state.qa_last_reply = reply or ""
        st.markdown("### 🧠 Assistant Reply")
        st.markdown(reply or "⚠️ No response received.")
