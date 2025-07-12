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

# -- SESSION STATE INIT --
st.session_state.setdefault("active_expander", None)

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
    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=prompt_text)
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID)

    with st.spinner("Assistant is reviewing the rules..."):
        while True:
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
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

# -- FUNCTION TO DISPLAY REPLY IN COLLAPSIBLE FORMAT --
def display_assistant_reply(assistant_reply):
    if not assistant_reply:
        st.warning("⚠️ No reply received from the assistant.")
        return
    if "### 🧠 Explanation" in assistant_reply:
        simplified = assistant_reply.split("### 🧠 Explanation")[-1].split("###")[0]
        st.markdown("### 🧠 Simplified Explanation (for players)")
        st.markdown(simplified.strip())
        st.markdown("---")
    if "### 📜 Rule Content" in assistant_reply:
        rule_section = assistant_reply.split("### 📜 Rule Content")[-1].split("###")[0]
        with st.expander("📜 View Full Rule Content", expanded=True):
            st.markdown(rule_section.strip())
    if "### 📎 Source" in assistant_reply:
        source_section = assistant_reply.split("### 📎 Source")[-1]
        with st.expander("📎 View Source Details", expanded=True):
            st.markdown(source_section.strip())
    with st.expander("🧾 Full Assistant Response (Formatted)", expanded=True):
        st.markdown(assistant_reply)

# ------------------------------
# 💬 GENERAL QUESTION INPUT
# ------------------------------
st.markdown("## 💬 Ask a Rules Question")

# Clear input box safely after rerun
if "clear_general" in st.session_state:
    del st.session_state["general_prompt"]
    del st.session_state["clear_general"]

# Render input
general_prompt = st.text_area(
    "Type your scenario or question:",
    placeholder="e.g., Can Team K recover their own punt?",
    key="general_prompt"
)
general_submit = st.button("Ask", key="general_submit")

# Handle submission
if general_prompt and general_submit:
    st.session_state.active_expander = "general"
    st.session_state["last_general_prompt"] = general_prompt
    st.session_state["last_general_reply"] = ask_assistant(general_prompt)
    st.session_state["clear_general"] = True
    st.rerun()

# Always show last question in collapsible expander
if "last_general_prompt" in st.session_state:
    with st.expander("👤 You asked (click to expand)", expanded=False):
        st.markdown(st.session_state["last_general_prompt"])

# Always show assistant reply if available
if "last_general_reply" in st.session_state:
    with st.chat_message("assistant"):
        display_assistant_reply(st.session_state["last_general_reply"])

# ------------------------------
# 🔍 RULE ID LOOKUP INPUT
# ------------------------------
st.markdown("---")
st.markdown("## 🔍 Look Up a Rule by ID")

# Clear rule input after rerun
if "clear_rule" in st.session_state:
    del st.session_state["rule_input"]
    del st.session_state["clear_rule"]

# Render rule input
rule_id_input = st.text_input("Enter Rule ID (e.g., 10-4-3 or 7-5-2e):", key="rule_input")
rule_submit = st.button("Look Up", key="rule_submit")

# Handle submission
if rule_id_input and rule_submit:
    st.session_state.active_expander = "rule_lookup"
    rule_prompt = f"Explain NFHS football rule {rule_id_input} from the 2025 rulebook. Include the rule text, its enforcement, and a simplified explanation suitable for players. Add case book examples if available."
    st.session_state["last_rule_prompt"] = rule_prompt
    st.session_state["last_rule_reply"] = ask_assistant(rule_prompt)
    st.session_state["clear_rule"] = True
    st.rerun()

# Always show last rule prompt
if "last_rule_prompt" in st.session_state:
    with st.expander("🔎 Rule Lookup Prompt (click to expand)", expanded=False):
        st.markdown(st.session_state["last_rule_prompt"])

# Always show last rule reply
if "last_rule_reply" in st.session_state:
    with st.chat_message("assistant"):
        display_assistant_reply(st.session_state["last_rule_reply"])
