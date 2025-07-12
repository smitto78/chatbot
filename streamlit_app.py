import streamlit as st
from openai import OpenAI
import time

# -- CONFIGURATION --
ASSISTANT_ID = "asst_AAbf5acxGSYy6NpApw2oqiZg"
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# -- PAGE SETTINGS --
st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="centered")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition (Stateless Mode)")
st.caption("Ask a question or look up a rule. Built for players, coaches, and officials.")

# -- CSS --
st.markdown("""
<style>
.greyed-out {
    color: gray;
    font-style: italic;
}
button[disabled] {
    pointer-events: none !important;
    opacity: 0.6 !important;
}
</style>
""", unsafe_allow_html=True)

# -- SESSION DEFAULTS --
defaults = {
    "general_input": "",
    "rule_input": "",
    "general_submitted": False,
    "rule_submitted": False,
    "general_processing": False,
    "rule_processing": False,
    "last_general_question": "",
    "last_general_response": "",
    "last_rule_id": "",
    "last_rule_response": ""
}
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# -- ASSISTANT CALL --
def ask_assistant(prompt_text):
    thread = client.beta.threads.create()
    client.beta.threads.messages.create(thread_id=thread.id, role="user", content=prompt_text)
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=ASSISTANT_ID)

    with st.spinner("Assistant is reviewing the rules..."):
        for _ in range(30):
            run_status = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                st.error("❌ Assistant run failed.")
                return None
            time.sleep(1)
        else:
            st.error("⚠️ Assistant timed out.")
            return None

    messages = client.beta.threads.messages.list(thread_id=thread.id)
    for msg in reversed(messages.data):
        if msg.role == "assistant" and msg.run_id == run.id:
            return msg.content[0].text.value
    return None

# -- DISPLAY REPLY --
def display_assistant_reply(reply):
    if not reply:
        st.warning("⚠️ No reply received.")
        return

    if "### 🧠 Explanation" in reply:
        simplified = reply.split("### 🧠 Explanation")[-1].split("###")[0]
        st.markdown("### 🧠 Simplified Explanation (for players)")
        st.markdown(simplified.strip())
        st.markdown("---")

    if "### 📜 Rule Content" in reply:
        rule_section = reply.split("### 📜 Rule Content")[-1].split("###")[0]
        with st.expander("📜 View Full Rule Content", expanded=True):
            st.markdown(rule_section.strip())

    if "### 📎 Source" in reply:
        source_section = reply.split("### 📎 Source")[-1]
        with st.expander("📎 View Source Details", expanded=True):
            st.markdown(source_section.strip())

    with st.expander("🧾 Full Assistant Response (Formatted)", expanded=True):
        st.markdown(reply)

# ----------------------------
# 💬 GENERAL QUESTION
# ----------------------------
st.markdown("## 💬 Ask a Rules Question")

if not st.session_state.general_submitted:
    st.session_state.general_input = st.text_area("Scenario or question:", value=st.session_state.general_input, key="general_input_box")
    ask_clicked = st.button("Ask", disabled=st.session_state.general_processing, key="ask_button")

    if ask_clicked and st.session_state.general_input.strip():
        st.session_state.general_processing = True
        st.session_state.last_general_question = st.session_state.general_input.strip()
        st.session_state.last_general_response = ask_assistant(st.session_state.last_general_question)
        st.session_state.general_submitted = True
        st.session_state.general_processing = False

if st.session_state.general_submitted:
    with st.expander("👤 You asked (click to collapse)", expanded=True):
        st.markdown(f"<div class='greyed-out'>{st.session_state.last_general_question}</div>", unsafe_allow_html=True)

    with st.chat_message("assistant"):
        display_assistant_reply(st.session_state.last_general_response)

    if st.button("🔄 Ask Another Question"):
        st.session_state.general_submitted = False
        st.session_state.general_input = ""
        st.session_state.last_general_question = ""
        st.session_state.last_general_response = ""

# ----------------------------
# 🔍 RULE LOOKUP
# ----------------------------
st.markdown("---")
st.markdown("## 🔍 Look Up a Rule by ID")

if not st.session_state.rule_submitted:
    st.session_state.rule_input = st.text_input("Enter Rule ID:", value=st.session_state.rule_input, key="rule_input_box")
    lookup_clicked = st.button("Look Up", disabled=st.session_state.rule_processing, key="lookup_button")

    if lookup_clicked and st.session_state.rule_input.strip():
        st.session_state.rule_processing = True
        st.session_state.last_rule_id = st.session_state.rule_input.strip()
        prompt = f"Explain NFHS football rule {st.session_state.last_rule_id} from the 2025 rulebook. Include the rule text, its enforcement, and a simplified explanation suitable for players. Add case book examples if available."
        st.session_state.last_rule_response = ask_assistant(prompt)
        st.session_state.rule_submitted = True
        st.session_state.rule_processing = False

if st.session_state.rule_submitted:
    with st.expander(f"🔎 Rule Lookup: {st.session_state.last_rule_id}", expanded=True):
        st.markdown(f"<div class='greyed-out'>{st.session_state.last_rule_id}</div>", unsafe_allow_html=True)

    with st.chat_message("assistant"):
        display_assistant_reply(st.session_state.last_rule_response)

    if st.button("🔄 Look Up Another Rule"):
        st.session_state.rule_submitted = False
        st.session_state.rule_input = ""
        st.session_state.last_rule_id = ""
        st.session_state.last_rule_response = ""
