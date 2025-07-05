import streamlit as st
from openai import OpenAI
import time

# -- CONFIGURATION --
ASSISTANT_ID = "asst_AAbf5acxGSYy6NpApw2oqiZg"

# -- INIT OPENAI CLIENT --
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# -- STREAMLIT PAGE SETTINGS --
st.set_page_config(page_title="🛠 NFHS Football 2025 Rules Assistant", layout="centered")
st.title("🛠 NFHS Football 2025 Rules Assistant (with Debug) v1.005")
st.caption(f"Connected to Assistant ID: `{ASSISTANT_ID}`")

# -- SESSION STATE INIT --
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id
    st.session_state.chat_history = []
    st.session_state.run_count = 0

# -- Display past messages --
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -- CHAT INPUT --
if prompt := st.chat_input("Say something to your assistant..."):

    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state.chat_history.append({"role": "user", "content": prompt})
    st.session_state.run_count += 1

    # ✅ ADD user message to thread
    response = client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt
    )
    st.code(f"[DEBUG] Added message ID: {response.id}")

    # ✅ RUN assistant
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id=ASSISTANT_ID
    )

    st.code(f"[DEBUG] Run ID: {run.id} (Run #{st.session_state.run_count})")

    # ✅ WAIT for completion
    with st.spinner("Waiting for assistant response..."):
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                st.error("❌ Assistant failed.")
                break
            time.sleep(1)

    # ✅ FETCH messages
    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)

    assistant_reply = None
    for message in reversed(messages.data):
        if message.role == "assistant" and message.run_id == run.id:
            assistant_reply = message.content[0].text.value
            st.code(f"[DEBUG] Assistant reply from message ID: {message.id}")
            break

    if assistant_reply:
        with st.chat_message("assistant"):
            st.markdown(assistant_reply)
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_reply})
    else:
        st.warning("⚠️ Assistant did not return a valid reply.")
