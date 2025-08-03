import time
import streamlit as st
from openai import OpenAI

# --- CONFIG ---
ASSISTANT_ID = "asst_AAbf5acxGSYy6NpApw2oqiZg"
RULE_PROMPT_ID = "pmpt_688eb6bb5d2c8195ae17efd5323009e0010626afbd178ad9"
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# --- PAGE SETUP ---
st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="wide")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition")
st.caption("Ask a question or look up a rule. Built for players, coaches, and officials.")

# --- SESSION STATE SETUP ---
default_keys = {
    "last_general_prompt": "",
    "last_general_reply": "",
    "last_rule_id": "",
    "thread_id": "",
}
for k, default in default_keys.items():
    st.session_state.setdefault(k, default)

# --- ASK FUNCTION ---
def ask_assistant(prompt: str, prompt_id: str = None) -> str | None:
    if not st.session_state.thread_id:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt
    )

    run_args = {
        "thread_id": st.session_state.thread_id,
        "assistant_id": ASSISTANT_ID,
    }
    if prompt_id:
        run_args["additional_instructions"] = {"prompt_id": prompt_id}

    run = client.beta.threads.runs.create(**run_args)

    with st.spinner("Assistant is reviewing the rules..."):
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

    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id).data
    for msg in reversed(messages):
        if msg.role == "assistant" and msg.run_id == run.id:
            return msg.content[0].text.value
    return None

# --- DISPLAY OUTPUT ---
def display_reply(reply: str):
    if not reply:
        st.warning("⚠️ No reply received.")
        return
    st.markdown("### 🧠 Assistant Reply")
    st.markdown(reply)

# --- GENERAL Q&A ---
def render_general_section():
    col1, col2 = st.columns([3, 1])
    with col1:
        prompt = st.text_area(
            "Type your scenario or question:",
            placeholder="e.g., Can Team K recover their own punt?",
            key="general_prompt"
        )
    with col2:
        if st.button("Ask"):
            st.session_state.last_general_prompt = st.session_state.general_prompt

    if st.session_state.last_general_prompt:
        reply = ask_assistant(st.session_state.last_general_prompt)
        st.session_state.last_general_reply = reply or ""
        display_reply(reply)

# --- RULE LOOKUP SECTION (Prompt-Driven) ---
def render_rule_section():
    st.markdown("---")
    rule_input = st.text_input("Enter Rule ID (e.g., 3-4-4j):", key="rule_input")
    if st.button("Look Up"):
        st.session_state.last_rule_id = rule_input.strip()

    if st.session_state.last_rule_id:
        rule_prompt = st.session_state.last_rule_id
        reply = ask_assistant(rule_prompt, prompt_id=RULE_PROMPT_ID)
        st.session_state.last_rule_id = ""
        display_reply(reply)

# --- MAIN RENDER ---
render_general_section()
render_rule_section()
