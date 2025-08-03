import time
import streamlit as st
from openai import OpenAI, trace

# --- CONFIG ---
RULE_PROMPT_ID = "pmpt_688eb6bb5d2c8195ae17efd5323009e0010626afbd178ad9"
VS_VECTOR_STORE_ID = "vs_688ed4dbc96081919239650f07d7046f"
ASSISTANT_ID = "asst_AAbf5acxGSYy6NpApw2oqiZg"
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# --- PAGE SETUP ---
st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="wide")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition")

# --- SESSION STATE ---
for key in ["thread_id", "last_general_prompt", "last_general_reply", "last_rule_id"]:
    st.session_state.setdefault(key, "")

# --- RULE LOOKUP FUNCTION ---
def ask_rule_lookup(rule_id: str) -> str | None:
    try:
        res = client.responses.create(
            prompt={"id": RULE_PROMPT_ID, "version": "29"},
            input=[{"role": "user", "content": f"id:{rule_id}"}],
            tools=[{"type": "file_search", "vector_store_ids": [VS_VECTOR_STORE_ID]}],
            text={"format": {"type": "text"}},
            max_output_tokens=2048,
            store=True
        )

        for out in res.output:
            if hasattr(out, "text") and hasattr(out.text, "value"):
                return out.text.value.strip()
            if hasattr(out, "content"):
                for block in out.content:
                    if hasattr(block, "text"):
                        return block.text.strip()

        return f"⚠️ No written response was generated for rule `{rule_id}`. Ensure it exists or improve your prompt."

    except Exception as e:
        st.error(f"❌ Rule lookup failed: {e}")
        return None

# --- GENERAL OPEN-ENDED QUESTION FUNCTION (with tracing) ---
def ask_general(prompt: str) -> str | None:
    if not st.session_state.thread_id:
        thread = client.beta.threads.create()
        st.session_state.thread_id = thread.id

    with trace.OpenAITelemetryTrace(name="nfhs-general-qna"):
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
        )

        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=ASSISTANT_ID
        )

        with st.spinner("Assistant is thinking..."):
            while True:
                status = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id,
                    run_id=run.id
                ).status
                if status == "completed":
                    break
                if status == "failed":
                    st.error("❌ Assistant run failed.")
                    return None
                time.sleep(1)

        msgs = client.beta.threads.messages.list(thread_id=st.session_state.thread_id).data
        for msg in reversed(msgs):
            if msg.role == "assistant" and msg.run_id == run.id:
                return msg.content[0].text.value
    return None

# --- RULE LOOKUP UI ---
def render_rule_section():
    st.markdown("## 🔍 Look Up a Rule by ID")
    rule_input = st.text_input("Enter Rule ID (e.g., 3-4-3d):", key="rule_input")
    if st.button("Look Up"):
        if rule_input.strip():
            result = ask_rule_lookup(rule_input.strip())
            st.markdown("### 📘 Rule Lookup Result")
            st.markdown(result or f"⚠️ No result returned for rule `{rule_input}`.")
        else:
            st.warning("Please enter a rule ID to look up.")

# --- GENERAL Q&A UI ---
def render_general_section():
    st.markdown("## 💬 Ask a Question About Rules or Scenarios")
    prompt = st.text_area("Enter a question or test-style scenario:",
                          placeholder="e.g., Can Team A recover their own punt after a muff?",
                          key="general_prompt")
    if st.button("Ask"):
        st.session_state.last_general_prompt = prompt.strip()

    if st.session_state.last_general_prompt:
        reply = ask_general(st.session_state.last_general_prompt)
        st.session_state.last_general_reply = reply or ""
        st.markdown("### 🧠 Assistant Reply")
        st.markdown(reply or "⚠️ No response received.")

# --- MAIN ---
render_general_section()
st.markdown("---")
render_rule_section()
