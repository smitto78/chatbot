import streamlit as st
from openai import OpenAI
import time

# -- CONFIGURATION --
ASSISTANT_ID = "asst_AAbf5acxGSYy6NpApw2oqiZg"

# -- INIT OPENAI CLIENT --
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# -- STREAMLIT PAGE SETTINGS --
st.set_page_config(page_title="🤖 Assistant Chat", layout="centered")
st.title("🤖 Assistant Chat")
st.caption(f"Connected to Assistant ID: `{ASSISTANT_ID}`")

# -- SESSION STATE INIT --
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# -- DISPLAY CHAT HISTORY --
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -- CHAT INPUT --
if prompt := st.chat_input("Ask your assistant..."):
    # Show user message in chat
    with st.chat_message("user"):
        st.markdown(prompt)

    # Save to local chat history
    st.session_state.chat_history.append({"role": "user", "content": prompt})

    # Send to assistant thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt
    )

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID
    )

    # Wait for run to complete
    with st.spinner("Assistant is thinking..."):
        while True:
            status = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
            if status.status == "completed":
                break
            elif status.status == "failed":
                st.error("❌ Assistant failed to respond.")
                break
            time.sleep(1)

    # Retrieve the latest assistant message specific to this run
    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
    for message in reversed(messages.data):
        if message.role == "assistant" and message.run_id == run.id:
            reply = message.content[0].text.value
            with st.chat_message("assistant"):
                st.markdown(reply)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})
            break
