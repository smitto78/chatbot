from openai.types.beta import Thread
from openai.types.beta.threads import Message
import time

# Initialize thread if it doesn't exist
if "thread_id" not in st.session_state:
    thread = client.beta.threads.create()
    st.session_state.thread_id = thread.id

# Read file contents if uploaded and send to assistant (optional)
if uploaded_file and "file_uploaded" not in st.session_state:
    file_content = read_file(uploaded_file)
    if file_content:
        # Save to a temporary file for upload
        with open(f"/tmp/{uploaded_file.name}", "w", encoding="utf-8") as f:
            f.write(file_content)
        # Upload the file to OpenAI
        uploaded = client.files.create(
            file=open(f"/tmp/{uploaded_file.name}", "rb"),
            purpose="assistants"
        )
        st.session_state.file_uploaded = uploaded.id
        st.success(f"✅ File '{uploaded_file.name}' uploaded to assistant.")

# User sends a message
if prompt := st.chat_input("Type your message here..."):
    with st.chat_message("user"):
        st.markdown(prompt)

    # Add message to thread
    client.beta.threads.messages.create(
        thread_id=st.session_state.thread_id,
        role="user",
        content=prompt,
        file_ids=[st.session_state.get("file_uploaded")] if "file_uploaded" in st.session_state else None
    )

    # Run the assistant
    run = client.beta.threads.runs.create(
        thread_id=st.session_state.thread_id,
        assistant_id="asst_AAbf5acxGSYy6NpApw2oqiZg"
    )

    # Wait for the run to complete
    with st.spinner("Assistant is thinking..."):
        while True:
            run_status = client.beta.threads.runs.retrieve(
                thread_id=st.session_state.thread_id,
                run_id=run.id
            )
            if run_status.status == "completed":
                break
            elif run_status.status == "failed":
                st.error("❌ Assistant failed to generate a response.")
                break
            time.sleep(1)

    # Retrieve messages
    messages = client.beta.threads.messages.list(thread_id=st.session_state.thread_id)
    for message in reversed(messages.data):
        if message.role == "assistant":
            with st.chat_message("assistant"):
                st.markdown(message.content[0].text.value)
            st.session_state.messages.append({
                "role": "assistant",
                "content": message.content[0].text.value
            })
            break

    st.session_state.messages.append({"role": "user", "content": prompt})
