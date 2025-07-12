import streamlit as st
from openai import OpenAI
import time

# -- CONFIGURATION --
ASSISTANT_ID = "asst_AAbf5acxGSYy6NpApw2oqiZg"
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# -- STREAMLIT PAGE SETTINGS --
st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="centered")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition")
st.caption("Ask a question or look up a rule. Built for players, coaches, and officials.")

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

# -- USER QUESTION INPUT --
prompt = st.chat_input("Ask your rules question (e.g., Can Team K recover their own punt?)")

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    assistant_reply = ask_assistant(prompt)

    if assistant_reply:
        with st.chat_message("assistant"):
            st.markdown(assistant_reply)

            if "### 🧠 Explanation" in assistant_reply:
                simplified = assistant_reply.split("### 🧠 Explanation")[-1].split("###")[0]
                st.markdown("---")
                st.markdown("### 🧠 Simplified Explanation (for players)")
                st.markdown(simplified.strip())

            if "### 📜 Rule Content" in assistant_reply:
                rule_section = assistant_reply.split("### 📜 Rule Content")[-1].split("###")[0]
                with st.expander("📜 View Full Rule Content"):
                    st.markdown(rule_section.strip())

            if "### 📎 Source" in assistant_reply:
                source_section = assistant_reply.split("### 📎 Source")[-1]
                with st.expander("📎 View Source Details"):
                    st.markdown(source_section.strip())
    else:
        st.warning("⚠️ No reply received from the assistant.")

# ------------------------------
# 🔍 RULE LOOKUP USING ASSISTANT
# ------------------------------
st.markdown("---")
with st.expander("🔍 Look Up a Rule by ID"):
    rule_id_input = st.text_input("Enter Rule ID (e.g., 10-4-3 or 7-5-2e):").strip()
    if rule_id_input:
        rule_prompt = f"Explain NFHS football rule {rule_id_input} from the 2025 rulebook. Include the rule text, its enforcement, and a simplified explanation suitable for players. Add case book examples if available."
        with st.chat_message("user"):
            st.markdown(f"🔎 Rule Lookup: **{rule_id_input}**")

        assistant_reply = ask_assistant(rule_prompt)

        if assistant_reply:
            with st.chat_message("assistant"):
                st.markdown(assistant_reply)

                if "### 🧠 Explanation" in assistant_reply:
                    simplified = assistant_reply.split("### 🧠 Explanation")[-1].split("###")[0]
                    st.markdown("---")
                    st.markdown("### 🧠 Simplified Explanation (for players)")
                    st.markdown(simplified.strip())

                if "### 📜 Rule Content" in assistant_reply:
                    rule_section = assistant_reply.split("### 📜 Rule Content")[-1].split("###")[0]
                    with st.expander("📜 View Full Rule Content"):
                        st.markdown(rule_section.strip())

                if "### 📎 Source" in assistant_reply:
                    source_section = assistant_reply.split("### 📎 Source")[-1]
                    with st.expander("📎 View Source Details"):
                        st.markdown(source_section.strip())
        else:
            st.warning("⚠️ No reply received for that rule lookup.")
