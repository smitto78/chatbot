import streamlit as st
from openai import OpenAI
from openai.types.chat import ChatCompletionChunk

# Initialize OpenAI client from secrets (configured in Streamlit Cloud)
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# App UI
st.title("💬 GPT-4.1 Nano Chatbot")
st.write("Ask me anything. Powered by `gpt-4.1-nano-2025-04-14`!")

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display previous messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle user input
if prompt := st.chat_input("Type your message here..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate response from OpenAI with streaming
    try:
        stream = client.chat.completions.create(
            model="gpt-4.1-nano-2025-04-14",
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )

        # Display assistant response as it streams
        with st.chat_message("assistant"):
            response_container = st.empty()
            full_response = ""

            for chunk in stream:
                content = chunk.choices[0].delta.content or ""
                full_response += content
                response_container.markdown(full_response + "▌")

            response_container.markdown(full_response)

        # Save assistant response to history
        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        st.error(f"⚠️ Error: {e}")
