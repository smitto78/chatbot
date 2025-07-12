import streamlit as st
from openai import OpenAI
import time

# -- CONFIGURATION --
ASSISTANT_ID = "asst_AAbf5acxGSYy6NpApw2oqiZg"
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# -- STREAMLIT PAGE SETTINGS --
st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="centered")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition (Stateless Mode)")
st.caption("Built for players, coaches, and officials – Ask a question and get a rule-supported answer.")

# -- UI TOGGLE FOR SIMPLIFICATION --
show_simple = st.toggle("👶 Simplified Explanation (for players)", value=False)

# -- USER PROMPT INPUT --
prompt = st.chat_input("Ask your rules question (e.g., Can Team K recover their own punt?)")

# -- PROCESS USER PROMPT --
if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)

    # 🔄 Create a new thread per question to ensure stateless behavior
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

    # ⏳ Wait until the assistant finishes responding
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

    # 📥 Fetch assistant's message from the completed thread
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    assistant_reply = None

    for message in reversed(messages.data):
        if message.role == "assistant" and message.run_id == run.id:
            assistant_reply = message.content[0].text.value
            break

    # 💬 Display the assistant's structured response
    if assistant_reply:
        with st.chat_message("assistant"):
            if show_simple and "### 🧠 Explanation" in assistant_reply:
                # Extract and show simplified explanation
                simplified = assistant_reply.split("### 🧠 Explanation")[-1].split("###")[0]
                st.markdown("### 🧠 Simplified Explanation")
                st.markdown(simplified.strip())
            else:
                st.markdown(assistant_reply)
    else:
        st.warning("⚠️ No reply received from the assistant.")
