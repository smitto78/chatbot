import time
import streamlit as st
from openai import OpenAI

ASSISTANT_ID = "asst_AAbf5acxGSYy6NpApw2oqiZg"
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="wide")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition")
st.caption("Ask a question or look up a rule. Built for players, coaches, and officials.")

# Initialize session state defaults
default_keys = {
    "last_general_prompt": "",
    "last_general_reply": "",
    "last_rule_id": "",
}
for k, default in default_keys.items():
    st.session_state.setdefault(k, default)

def ask_assistant(prompt: str) -> str | None:
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=prompt)
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID)
    with st.spinner("Assistant is reviewing the rules..."):
        while True:
            status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id).status
            if status == "completed":
                break
            if status == "failed":
                st.error("❌ Assistant run failed.")
                return None
            time.sleep(1)
    msgs = client.beta.threads.messages.list(thread_id=thread.id).data
    for msg in reversed(msgs):
        if msg.role == "assistant" and msg.run_id == run.id:
            return msg.content[0].text.value
    return None

def display_reply(reply: str):
    if not reply:
        st.warning("⚠️ No reply received.")
        return
    parts = reply.split("### 🧠 Explanation")
    if len(parts) > 1:
        explanation = parts[1].split("###")[0].strip()
        st.markdown("### 🧠 Simplified Explanation (for players)")
        st.markdown(explanation)
        st.markdown("---")
    if "### 📜 Rule Content" in reply:
        section = reply.split("### 📜 Rule Content")[-1].split("###")[0].strip()
        with st.expander("📜 Full Rule Content", expanded=True):
            st.markdown(section)
    if "### 📎 Source" in reply:
        src = reply.split("### 📎 Source")[-1].strip()
        with st.expander("📎 Source Details", expanded=True):
            st.markdown(src)
    with st.expander("🧾 Full Assistant Response (click to expand)", expanded=False):
        st.markdown(reply)

def render_general_section():
    col1, col2 = st.columns([3, 1])
    with col1:
        prompt = st.text_area("Type your scenario or question:", placeholder="e.g., Can Team K recover their own punt?", key="general_prompt")
    with col2:
        if st.button("Ask"):
            st.session_state.last_general_prompt = st.session_state.general_prompt
    if st.session_state.last_general_prompt:
        reply = ask_assistant(st.session_state.last_general_prompt)
        st.session_state.last_general_reply = reply or ""
        display_reply(reply)

def render_rule_section():
    st.markdown("---")
    rule_input = st.text_input("Enter Rule ID (e.g., 7‑5‑2e):", key="rule_input")
    if st.button("Look Up"):
        st.session_state.last_rule_id = rule_input
    if st.session_state.last_rule_id:
        rule_id = st.session_state.last_rule_id
        rule_prompt = (
            f"You are an NFHS football rules expert. A user has asked about rule {rule_id} from the 2025 rulebook.\n\n"
            f"Step 1: Check the retrieved document. Only respond if `metadata.id` is exactly equal to \"{rule_id}\".\n"
            f"Step 2: If the ID matches, format your reply like this:\n\n"
            f"NFHS Rule {rule_id}:\n\n"
            f"**Rule Title:** [Insert metadata.rule_title if available]\n"
            f"**Rule Text:** [Insert the `text` field as-is]\n\n"
            f"**Additional Notes:**\n"
            f"- Include helpful clarifications or common field rulings as bullet points (if applicable)\n\n"
            f"Step 3: If the ID does not match exactly, say:\n"
            f"\"Rule {rule_id} was not found in the 2025 NFHS Rulebook.\"\n"
            f"Do not guess. Do not summarize nearby rules. Do not infer based on similarity.\n\n"
            f"Also: Always include this debug line at the top: `Retrieved metadata.id: [actual ID]`"
        )
        reply = ask_assistant(rule_prompt)
        st.session_state.last_rule_id = ""
        display_reply(reply)

# Main layout
render_general_section()
render_rule_section()
