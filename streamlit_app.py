import streamlit as st
from openai import OpenAI
import time

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

# -- SESSION STATE INIT --
if "active_expander" not in st.session_state:
    st.session_state.active_expander = None

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
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                st.error("❌ Assistant run failed.")
                return None
            time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    for message in reversed(messages.data):
        if message.role == "assistant" and message.run_id == run.id:
            return message.content[0].text.value
    return None

# -- FUNCTION TO DISPLAY REPLY IN UNIFIED FORMAT --
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
        with st.expander("📜 View Full Rule Content"):
            st.markdown(rule_section.strip())

    # Source Expander
    if "### 📎 Source" in assistant_reply:
        source_section = assistant_reply.split("### 📎 Source")[-1]
        with st.expander("📎 View Source Details"):
            st.markdown(source_section.strip())

    # Show full reply at the bottom for transparency
    with st.expander("🧾 Full Assistant Response (Formatted)"):
        st.markdown(assistant_reply)

# ------------------------------
# 💬 GENERAL RULE QUESTION
# ------------------------------
st.markdown("## 💬 Ask a Rules Question")

with st.expander("Ask about a scenario or rule enforcement (e.g., roughing the passer, PSK, muffed punt):", expanded=st.session_state.active_expander == "general"):
    general_prompt = st.text_area("Type your question here:", placeholder="Can Team K recover their own punt?")
    general_submit = st.button("Ask", key="general_ask")

if general_prompt and general_submit:
    st.session_state.active_expander = "general"
    st.markdown("**👤 You asked:**")
    st.markdown(general_prompt)
    general_reply = ask_assistant(general_prompt)
    with st.chat_message("assistant"):
        display_assistant_reply(general_reply)

# ------------------------------
# 🔍 RULE LOOKUP USING ASSISTANT
# ------------------------------
st.markdown("---")
st.markdown("## 🔍 Look Up a Rule by ID")

with st.expander("Look up a specific rule number (e.g., 10-4-3 or 7-5-2e):", expanded=st.session_state.active_expander == "rule_lookup"):
    rule_id_input = st.text_input("Enter Rule ID:")
    rule_submit = st.button("Look Up", key="rule_lookup_button")

if rule_id_input and rule_submit:
    st.session_state.active_expander = "rule_lookup"
    rule_prompt = f"Explain NFHS football rule {rule_id_input} from the 2025 rulebook. Include the rule text, its enforcement, and a simplified explanation suitable for players. Add case book examples if available."
    st.markdown(f"🔎 Rule Lookup: **{rule_id_input}**")
    rule_reply = ask_assistant(rule_prompt)
    with st.chat_message("assistant"):
        display_assistant_reply(rule_reply)
