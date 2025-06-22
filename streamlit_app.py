import streamlit as st
from openai import OpenAI
import time

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# Assistant ID
ASSISTANT_ID = "asst_AAbf5acxGSYy6NpApw2oqiZg"

st.set_page_config(page_title="Assistant Chat", layout="centered")
st.title("🤖 Assistant Chat")
st.caption("Connected to Assistant ID: " + ASSISTANT_ID)

# Initialize thread
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.session_state.chat_history = []

# Show previous messages
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
if prompt := st.chat_input("Say something..."):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add to thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt
    )

    # Run assistant
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID
    )

    # Wait for run to complete
    with st.spinner("Thinking..."):
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                st.error("Assistant failed.")
                break
            time.sleep(1)

    # Get assistant message
    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
    for message in reversed(messages.data):
        if message.role == "assistant":
            assistant_reply = message.content[0].text.value
            with st.chat_message("assistant"):
                st.markdown(assistant_reply)
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})
            break
