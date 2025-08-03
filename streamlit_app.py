import time
import streamlit as st
from openai import OpenAI

# --- CONFIG ---
ASSISTANT_ID = "asst_AAbf5acxGSYy6NpApw2oqiZg"
RULE_PROMPT_ID = "pmpt_688eb6bb5d2c8195ae17efd5323009e0010626afbd178ad9"
VS_VECTOR_STORE_ID = "vs_68883bb7d06881918ceeaa63a83f4725"
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# --- PAGE SETUP ---
st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="wide")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition")
st.caption("Ask a question or look up a rule. Built for players, coaches, and officials.")

# --- SESSION STATE ---
for key in ["thread_id", "last_general_prompt", "last_general_reply", "last_rule_id"]:
    st.session_state.setdefault(key, "")

# --- GENERAL QUESTION FUNCTION ---
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

    with st.spinner("Assistant is reviewing..."):
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

# --- RULE LOOKUP FUNCTION (via prompt & vector) ---
def ask_rule_lookup(rule_id: str) -> str | None:
    try:
        res = client.responses.create(
            prompt={"id": RULE_PROMPT_ID, "version": "6"},
            input=[{"role": "user", "content": f"What does rule {rule_id} say?"}],
            tools=[{
                "type": "file_search",
                "vector_store_ids": [VS_VECTOR_STORE_ID]
            }],
            max_output_tokens=2048,
            store=False
        )
        return getattr(res, "text", None)
    except Exception as e:
        st.error(f"❌ Rule lookup failed: {e}")
        return None

# --- UI SECTION HANDLERS ---
def render_general_section():
    col1, col2 = st.columns([3, 1])
    with col1:
        prompt = st.text_area("Type your scenario or question:",
                              placeholder="e.g., Can Team K recover their own punt?",
                              key="general_prompt")
    with col2:
        if st.button("Ask"):
            st.session_state.last_general_prompt = st.session_state.general_prompt

    if st.session_state.last_general_prompt:
        reply = ask_general(st.session_state.last_general_prompt)
        st.session_state.last_general_reply = reply or ""
        st.markdown("### 🧠 Assistant Reply")
        st.markdown(reply or "")

def render_rule_section():
    st.markdown("---")
    rule_input = st.text_input("Enter Rule ID (e.g., 3‑4‑4j):", key="rule_input")
    if st.button("Look Up"):
        st.session_state.last_rule_id = rule_input.strip()

    if st.session_state.last_rule_id:
        reply = ask_rule_lookup(st.session_state.last_rule_id)
        st.session_state.last_rule_id = ""
        st.markdown("### 🔍 Rule Lookup Result")
        st.markdown(reply or f"Rule ID not found.")

# --- MAIN ---
render_general_section()
render_rule_section()
