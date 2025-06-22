import streamlit as st
from openai import OpenAI
import docx2txt
import PyPDF2
import os
import time

# Initialize OpenAI client
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

st.set_page_config(page_title="💬 GPT Assistant with File Review", layout="centered")
st.title("💬 GPT Assistant with File Review")
st.write("Ask anything or upload a file. Powered by Assistants API!")

# Setup session state
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

if "messages" not in st.session_state:
    st.session_state.messages = []

# File reader
def read_file(file):
    if file.type == "text/plain":
        return file.read().decode("utf-8")
    elif file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return docx2txt.process(file)
    return None

# File upload
uploaded_file = st.file_uploader("📎 Upload .txt, .pdf, or .docx file", type=["txt", "pdf", "docx"])

if uploaded_file and "file_uploaded" not in st.session_state:
    content = read_file(uploaded_file)
    if content:
        with open(f"/tmp/{uploaded_file.name}", "w", encoding="utf-8") as f:
            f.write(content)
        uploaded = client.files.create(file=open(f"/tmp/{uploaded_file.name}", "rb"), purpose="assistants")
        st.session_state.file_uploaded = uploaded.id
        st.success(f"✅ File '{uploaded_file.name}' uploaded to assistant context.")
    else:
        st.error("❌ Failed to read file content.")

# Display past messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Type your message..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add user message to thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt,
        file_ids=[st.session_state["file_uploaded"]] if "file_uploaded" in st.session_state else None
    )

    # Run assistant
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id="asst_AAbf5acxGSYy6NpApw2oqiZg"
    )

    with st.spinner("Assistant is thinking..."):
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                st.error("❌ Assistant run failed.")
                break
            time.sleep(1)

    # Get assistant reply
    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
    for msg in reversed(messages.data):
        if msg.role == "assistant":
            reply = msg.content[0].text.value
            with st.chat_message("assistant"):
                st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            break

    st.session_state.messages.append({"role": "user", "content": prompt})
