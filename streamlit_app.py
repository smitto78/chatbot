import time
import streamlit as st
from openai import OpenAI

# --- CONFIG ---
ASSISTANT_ID = "asst_AAbf5acxGSYy6NpApw2oqiZg"
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# --- SESSION STATE ---
for key in ["thread_id", "last_general_prompt", "last_general_reply", "last_rule_id"]:
    st.session_state.setdefault(key, "")

# --- GENERAL OPEN-ENDED RULE Q&A ---
def ask_general(prompt: str) -> str | None:
    if not st.session_state.thread_id:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt
    )

    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID
    )

    with st.spinner("Assistant is thinking..."):
        while True:
            status = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            ).status
            if status == "completed":
                break
            if status == "failed":
                st.error("❌ Assistant run failed.")
                return None
            time.sleep(1)

    msgs = client.beta.threads.messages.list(thread_id=st.session_state.thread_id).data
    for msg in reversed(msgs):
        if msg.role == "assistant" and msg.run_id == run.id:
            return msg.content[0].text.value
    return None

# --- UI SECTION: GENERAL RULE QUESTIONS ---
def render_general_section():
    st.markdown("## 💬 Ask About Rules or Case Interpretations")
    prompt = st.text_area("Type a scenario, rule question, or case interpretation:",
                          placeholder="e.g., Can Team A advance a muffed free kick?",
                          key="general_prompt")
    if st.button("Ask", key="ask_general"):
        st.session_state.last_general_prompt = prompt.strip()

    if st.session_state.last_general_prompt:
        reply = ask_general(st.session_state.last_general_prompt)
        st.session_state.last_general_reply = reply or ""
        st.markdown("### 🧠 Assistant Reply")
        st.markdown(reply or "No response received.")

st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="wide")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition")
st.caption("Look up rules by ID or ask scenario-based questions to prepare for game day or exams.")

render_general_section()
st.markdown("---")
