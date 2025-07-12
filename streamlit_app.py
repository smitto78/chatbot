import streamlit as st
from openai import OpenAI
import time
import re

# -- CONFIGURATION --
ASSISTANT_ID = "asst_AAbf5acxGSYy6NpApw2oqiZg"
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# -- STREAMLIT PAGE SETTINGS --
st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="centered")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition (Stateless Mode)")
st.caption("Ask a question or look up a rule. Built for players, coaches, and officials.")

# -- STYLING (OPTIONAL) --
st.markdown("""
<style>
h3 {
    margin-top: 1.2em;
    color: #003366;
}
</style>
""", unsafe_allow_html=True)

# -- GENERAL FUNCTION FOR HANDLING PROMPTS --
def ask_assistant(prompt_text):
    thread = client.beta.threads.create()

    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt_text
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    with st.spinner("Assistant is reviewing the rules..."):
        max_retries = 30
        retry_count = 0
        while retry_count < max_retries:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                st.error("❌ Assistant run failed.")
                return None
            retry_count += 1
            time.sleep(1)
        else:
            st.error("⚠️ Assistant timed out.")
            return None

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    for message in reversed(messages.data):
        if message.role == "assistant" and message.run_id == run.id:
            return message.content[0].text.value
    return None

# -- FUNCTION TO DISPLAY REPLY IN COLLAPSIBLE FORMAT --
def display_assistant_reply(assistant_reply):
    if not assistant_reply:
        st.warning("⚠️ No reply received from the assistant.")
        return

    # Always show simplified explanation first
    if "### 🧠 Explanation" in assistant_reply:
        simplified = assistant_reply.split("### 🧠 Explanation")[-1].split("###")[0]
        st.markdown("### 🧠 Simplified Explanation (for players)")
        st.markdown(simplified.strip())
        st.markdown("---")

    # Rule Content Expander
    if "### 📜 Rule Content" in assistant_reply:
        rule_section = assistant_reply.split("### 📜 Rule Content")[-1].split("###")[0]
        with st.expander("📜 View Full Rule Content", expanded=True):
            st.markdown(rule_section.strip())

    # Source Expander
    if "### 📎 Source" in assistant_reply:
        source_section = assistant_reply.split("### 📎 Source")[-1]
        with st.expander("📎 View Source Details", expanded=True):
            st.markdown(source_section.strip())

    # Full Response
    with st.expander("🧾 Full Assistant Response (Formatted)", expanded=False):
        st.markdown(assistant_reply)

# ------------------------------
# 💬 GENERAL QUESTION INPUT
# ------------------------------
st.markdown("## 💬 Ask a Rules Question")

with st.form("general_form", clear_on_submit=True):
    general_prompt = st.text_area(
        "Type your scenario or question:",
        placeholder="e.g., Can Team K recover their own punt?",
        key="general_prompt_input"
    )
    general_submit = st.form_submit_button("Ask")

if general_submit and general_prompt:
    with st.expander("👤 You asked (click to expand)", expanded=False):
        st.markdown(general_prompt)
    general_reply = ask_assistant(general_prompt)
    with st.chat_message("assistant"):
        display_assistant_reply(general_reply)

# ------------------------------
# 🔍 RULE ID LOOKUP INPUT
# ------------------------------
st.markdown("---")
st.markdown("## 🔍 Look Up a Rule by ID")

with st.form("rule_lookup_form", clear_on_submit=True):
    rule_id_input = st.text_input(
        "Enter Rule ID (e.g., 10-4-3 or 7-5-2e):",
        key="rule_id_input"
    )
    rule_submit = st.form_submit_button("Look Up")

if rule_submit and rule_id_input:
    rule_prompt = f"Explain NFHS football rule {rule_id_input} from the 2025 rulebook. Include the rule text, its enforcement, and a simplified explanation suitable for players. Add case book examples if available."
    with st.expander(f"🔎 Rule Lookup: {rule_id_input} (click to expand)", expanded=False):
        st.markdown(rule_prompt)
    rule_reply = ask_assistant(rule_prompt)
    with st.chat_message("assistant"):
        display_assistant_reply(rule_reply)
