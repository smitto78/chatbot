import re
import time
import streamlit as st
from openai import OpenAI

# --- CONFIG ---
ASSISTANT_ID = "asst_AAbf5acxGSYy6NpApw2oqiZg"
RULE_PROMPT_ID = "pmpt_688eb6bb5d2c8195ae17efd5323009e0010626afbd178ad9"
VECTOR_STORE_ID = "vs_688ed4dbc96081919239650f07d7046f"
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# --- SESSION STATE ---
for key in ["thread_id", "last_prompt", "last_reply", "last_rule_id", "last_rule_result"]:
    st.session_state.setdefault(key, "")

# --- RULE ID DETECTION ---
def is_rule_id(text: str) -> bool:
    return bool(re.match(r"^\d+-\d+(?:-\d+[a-z]?)?$", text.strip()))

# --- RULE REFERENCE PARSING ---
def extract_rule_reference(text: str) -> str | None:
    match = re.search(r"Rule Reference: ([\w-]+)", text)
    return match.group(1).strip() if match else None

def rule_ids_match(requested: str, returned: str) -> bool:
    return requested.strip().lower() == returned.strip().lower()

# --- RULE LOOKUP FUNCTION (Exact Match via Responses API) ---
def ask_rule_lookup(rule_id: str) -> str | None:
    try:
        res = client.responses.create(
            prompt={"id": RULE_PROMPT_ID, "version": "32"},
            input=[{"role": "user", "content": f"id:{rule_id}"}],
            tools=[{
                "type": "file_search",
                "vector_store_ids": [VECTOR_STORE_ID],
                "filters": {
                    "type": "and",
                    "filters": [{
                        "type": "eq",
                        "key": "rule_id",
                        "value": rule_id
                    }]
                },
                "max_num_results": 1
            }],
            text={"format": {"type": "text"}},
            temperature=0.2,
            max_output_tokens=2048,
            store=True
        )

        for out in res.output:
            if text := getattr(getattr(out, "text", None), "value", None):
                return text.strip()
        return f"⚠️ No response generated for rule `{rule_id}`."

    except Exception as e:
        st.error(f"❌ Rule lookup failed: {e}")
        return None

# --- GENERAL Q&A FUNCTION ---
def ask_general(prompt: str) -> str | None:
    try:
        if not st.session_state.thread_id:
            thread = client.beta.threads.create()
            st.session_state.thread_id = thread.id

        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id,
            role="user",
            content=prompt
        )

        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=ASSISTANT_ID,
            temperature=0.7
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
    except Exception as e:
        st.error(f"❌ Assistant error: {e}")
        return None

# --- UI SECTION ---
def render_main():
    st.markdown("## 💬 Ask About Rules or Look Up by ID")
    prompt = st.text_area("Type a rule ID (e.g., 8-5-3c) or scenario/question:",
                          key="user_prompt")

    if st.button("Submit", key="submit_prompt"):
        query = prompt.strip()
        if is_rule_id(query):
            st.session_state.last_rule_id = query
            st.session_state.last_rule_result = ask_rule_lookup(query)
            st.session_state.last_prompt = ""
            st.session_state.last_reply = ""
        else:
            st.session_state.last_prompt = query
            st.session_state.last_reply = ask_general(query)
            st.session_state.last_rule_id = ""
            st.session_state.last_rule_result = ""

    # --- Show Responses ---
    if st.session_state.last_rule_id and st.session_state.last_rule_result:
        rule_ref = extract_rule_reference(st.session_state.last_rule_result)
        if rule_ref:
            st.markdown(f"### 📘 Rule Lookup: {rule_ref}")
            if not rule_ids_match(st.session_state.last_rule_id, rule_ref):
                st.warning(
                    f"The assistant returned **{rule_ref}**, which may not match your input `{st.session_state.last_rule_id}`. Please verify the result."
                )
        else:
            st.markdown(f"### 📘 Rule Lookup: {st.session_state.last_rule_id}")

        st.markdown(st.session_state.last_rule_result)

    elif st.session_state.last_prompt and st.session_state.last_reply:
        st.markdown("### 🧠 Assistant Reply")
        st.markdown(st.session_state.last_reply)

# --- PAGE CONFIG ---
st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="wide")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition")
st.caption("Ask rule questions or look up by ID. Powered by OpenAI's Assistant API.")

# --- MAIN ---
render_main()
