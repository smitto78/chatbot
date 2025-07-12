import streamlit as st
from openai import OpenAI
import time

# -- CONFIGURATION --
ASSISTANT_ID = "asst_AAbf5acxGSYy6NpApw2oqiZg"
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# -- STREAMLIT PAGE SETTINGS --
st.set_page_config(page_title="🛠 NFHS Football 2025 Rules Assistant", layout="centered")
st.title("🛠 NFHS Football 2025 Rules Assistant (Stateless Mode)")
st.caption("Each question is treated independently. No memory is retained between questions.")

# -- USER PROMPT --
prompt = st.chat_input("Ask a rules question (e.g., PSK enforcement, illegal touching)...")

# -- PROCESS QUESTION --
if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    # 🔄 NEW THREAD PER QUESTION (stateless mode)
    thread = client.beta.threads.create()

    # ➕ Add user message to the new thread
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

    # ⏳ Wait for run to complete
    with st.spinner("Assistant is thinking..."):
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

    # 📥 Fetch messages from the thread
    messages = client.beta.threads.messages.list(thread_id=thread.id)

    # 💬 Display assistant reply
    for message in reversed(messages.data):
        if message.role == "assistant" and message.run_id == run.id:
            assistant_reply = message.content[0].text.value
            with st.chat_message("assistant"):
                st.markdown(assistant_reply)
            break
