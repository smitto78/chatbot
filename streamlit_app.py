import streamlit as st
from openai import OpenAI
from openai.types.chat import ChatCompletionChunk

import docx2txt
import PyPDF2
import io

# Initialize OpenAI client from Streamlit secrets
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# App UI
st.title("💬 GPT-4.1 Nano Chatbot with File Review")
st.write("Ask anything or upload a file. Powered by `gpt-4.1-nano-2025-04-14`!")

# File upload
uploaded_file = st.file_uploader("📎 Drag and drop or select a file for review", type=["txt", "pdf", "docx"])

# Read file contents if uploaded
def read_file(file):
    if file.type == "text/plain":
        return file.read().decode("utf-8")
    elif file.type == "application/pdf":
        reader = PyPDF2.PdfReader(file)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
    elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return docx2txt.process(file)
    else:
        return None

# Initialize chat session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# If a file is uploaded, include its contents in the context
if uploaded_file:
    file_content = read_file(uploaded_file)
    if file_content:
        system_message = f"The user uploaded a file. Here is its content:\n\n{file_content[:4000]}"
        st.session_state.messages.append({"role": "system", "content": system_message})
        st.success(f"✅ File '{uploaded_file.name}' was uploaded and added to the context.")
    else:
        st.error("❌ Unable to read the file content.")

# Chat input
if prompt := st.chat_input("Type your message here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        stream = client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )

        with st.chat_message("assistant"):
            response_container = st.empty()
            full_response = ""

            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                full_response += content
                response_container.markdown(full_response + "▌")

            response_container.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
