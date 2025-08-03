import time
import streamlit as st
from openai import OpenAI

# --- CONFIG ---
RULE_PROMPT_ID = "pmpt_688eb6bb5d2c8195ae17efd5323009e0010626afbd178ad9"
VS_VECTOR_STORE_ID = "vs_68883bb7d06881918ceeaa63a83f4725"
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

# --- RULE ID LOOKUP USING FILE SEARCH PROMPT ---
def ask_rule_lookup(rule_id: str) -> str | None:
    try:
        response = client.responses.create(
            prompt={
                "id": RULE_PROMPT_ID,
                "version": "latest",
                "variables": {"rule_id": rule_id}
            },
            input=[{
                "role": "user",
                "content": f"id:{rule_id}"
            }],
            tools=[{
                "type": "file_search",
                "vector_store_ids": [VS_VECTOR_STORE_ID]
            }],
            max_output_tokens=2048,
            store=False
        )

        for item in response.output:
            if hasattr(item, "text") and item.text.value.strip():
                return item.text.value.strip()

        return f"⚠️ No written response was generated for rule {rule_id}. Ensure it exists or improve your prompt."
    except Exception as e:
        st.error(f"❌ Rule lookup failed: {e}")
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

# --- UI SECTION: RULE ID LOOKUP ---
def render_rule_section():
    st.markdown("## 📘 Look Up a Rule by ID")
    rule_input = st.text_input("Enter Rule ID (e.g., 3-4-3a):", key="rule_input")
    if st.button("Look Up", key="ask_rule"):
        st.session_state.last_rule_id = rule_input.strip()

    if st.session_state.last_rule_id:
        result = ask_rule_lookup(st.session_state.last_rule_id)
        st.session_state.last_rule_id = ""
        st.markdown("### 📘 Rule Lookup Result")
        st.markdown(result or f"⚠️ No result returned for rule `{rule_input}`.")

# --- MAIN ---
st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="wide")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition")
st.caption("Look up rules by ID or ask scenario-based questions to prepare for game day or exams.")

render_general_section()
st.markdown("---")
render_rule_section()
