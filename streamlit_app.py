import streamlit as st
from openai import OpenAI
from openai.types.chat import ChatCompletionChunk

# Load the OpenAI API key from Streamlit secrets
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# App title and instructions
st.title("💬 GPT-4.1 Nano Chatbot")
st.write("Ask me anything. I'm powered by `gpt-4.1-nano-2025-04-14`!")

# Initialize chat session
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User input
if prompt := st.chat_input("Type your message here..."):
    # Store and show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate assistant reply
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
                if isinstance(chunk, ChatCompletionChunk):
                    content = chunk.choices[0].delta.get("content", "")
                    full_response += content
                    response_container.markdown(full_response + "▌")

            response_container.markdown(full_response)

        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
    