import time
import streamlit as st
from openai import OpenAI

# --- CONFIG ---
ASSISTANT_ID = "asst_AAbf5acxGSYy6NpApw2oqiZg"
VECTOR_FILE_ID = "file-Py3QLxmV7Mmu81K2a6WqQG"  # ← replace with your uploaded file ID
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

# --- ASK FUNCTION WITH SESSION + VECTOR FILE SUPPORT ---
def ask_assistant(prompt: str) -> str | None:
    if not st.session_state.thread_id:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt,
        file_ids=[VECTOR_FILE_ID]  # ✅ Moved here
    )

    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID
        # ❌ Do NOT include file_ids here
    )

    with st.spinner("Assistant is reviewing the rules..."):
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            ).status
            if run_status == "completed":
                break
            if run_status == "failed":
                st.error("❌ Assistant run failed.")
                return None
            time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id).data
    for msg in reversed(messages):
        if msg.role == "assistant" and msg.run_id == run.id:
            return msg.content[0].text.value
    return None


# --- DISPLAY OUTPUT CLEANLY ---
def display_reply(reply: str):
    if not reply:
        st.warning("⚠️ No reply received.")
        return
    st.markdown("### 🧠 Assistant Reply")
    st.markdown(reply)

# --- GENERAL SCENARIO SECTION ---
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

# --- RULE LOOKUP SECTION ---
def render_rule_section():
    st.markdown("---")
    rule_input = st.text_input("Enter Rule ID (e.g., 3-4-4j):", key="rule_input")
    if st.button("Look Up"):
        st.session_state.last_rule_id = rule_input.strip()

    if st.session_state.last_rule_id:
        rule_id = st.session_state.last_rule_id
        rule_prompt = (
            f"You are an NFHS football rules expert. The user is asking about rule {rule_id} from the 2025 rulebook.\n\n"
            f"Step 1: Search the uploaded rules file for entries where the metadata field `id` is exactly \"{rule_id}\".\n"
            f"Step 2: If such an entry is found, use the `text` as the rule's definition. Present your answer in this format:\n\n"
            f"NFHS Rule {rule_id} defines the term or topic it addresses. Here is the rule:\n\n"
            f"Rule {rule_id}: [insert exact rule text here]\n\n"
            f"Further key points often included in this rule:\n"
            f"- [Insert helpful clarifications or common rulings as bullet points]\n\n"
            f"Step 3: If no rule with `id` exactly matching \"{rule_id}\" is found, say:\n"
            f"\"Rule {rule_id} was not found in the 2025 NFHS Rulebook.\"\n"
            f"Do not guess or assume. Only respond if there is an exact `id` match."
        )
        reply = ask_assistant(rule_prompt)
        st.session_state.last_rule_id = ""
        display_reply(reply)

# --- MAIN RENDER ---
render_general_section()
render_rule_section()