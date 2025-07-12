import streamlit as st
from openai import OpenAI
import time

# -- CONFIGURATION --
ASSISTANT_ID = "asst_AAbf5acxGSYy6NpApw2oqiZg"
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# -- STREAMLIT PAGE SETTINGS --
st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="centered")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition")
st.caption("Ask a question and receive an official, rule-supported answer. Designed for players, coaches, and officials.")

# -- USER PROMPT INPUT --
prompt = st.chat_input("Ask your rules question (e.g., Can Team K recover their own punt?)")

# -- PROCESS USER PROMPT --
if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    # 🔄 Create new thread per question (stateless mode)
    thread = client.beta.threads.create()

    # ➕ Add user message to thread
    client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt
    )

    # ▶️ Run assistant
    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=ASSISTANT_ID
    )

    # ⏳ Wait for completion
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
                break
            time.sleep(1)

    # 📥 Retrieve messages
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    assistant_reply = None

    for message in reversed(messages.data):
        if message.role == "assistant" and message.run_id == run.id:
            assistant_reply = message.content[0].text.value
            break

    # 💬 Display assistant reply and simplified explanation
    if assistant_reply:
        with st.chat_message("assistant"):
            # Display full structured reply
            st.markdown(assistant_reply)

            # Simplified explanation from Explanation section
            if "### 🧠 Explanation" in assistant_reply:
                simplified = assistant_reply.split("### 🧠 Explanation")[-1].split("###")[0]
                st.markdown("---")
                st.markdown("### 🧠 Simplified Explanation (for players)")
                st.markdown(simplified.strip())

            # Rule content expander
            if "### 📜 Rule Content" in assistant_reply:
                rule_section = assistant_reply.split("### 📜 Rule Content")[-1].split("###")[0]
                with st.expander("📜 View Full Rule Content"):
                    st.markdown(rule_section.strip())

            # Source section expander
            if "### 📎 Source" in assistant_reply:
                source_section = assistant_reply.split("### 📎 Source")[-1]
                with st.expander("📎 View Source Details"):
                    st.markdown(source_section.strip())
    else:
        st.warning("⚠️ No reply received from the assistant.")

# ------------------------------
# 🔍 Rule Reference Lookup Tool
# ------------------------------
st.markdown("---")
with st.expander("🔍 Look Up a Rule by ID (for officials or trainers)"):
    rule_id_input = st.text_input("Enter Rule ID (e.g., 10-4-3 or 7-5-2e):")
    if rule_id_input:
        st.info("⚠️ Rule lookup is not yet connected to your rules database. This feature is a placeholder for future integration.")
