import time
import asyncio
import os
import streamlit as st
from openai import OpenAI
from typing import Optional
from agents import Agent, Runner, set_default_openai_key
from agents.tracing import trace


# © 2025 Tommy Smith. All Rights Reserved.
# NFHS Football Rules Assistant – 2025 Edition
# Unauthorized copying, modification, distribution, or use of this software is prohibited.


# --- ENVIRONMENT SETUP ---
os.environ["OPENAI_TRACING_ENABLED"] = "true"

# --- API KEYS ---
set_default_openai_key(st.secrets["openai"]["api_key"])
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# --- CONFIGURATION ---
CONFIG = {
    "RULE_PROMPT_ID": "pmpt_688eb6bb5d2c8195ae17efd5323009e0010626afbd178ad9",
    "VECTOR_STORE_ID": "vs_689558cb487c819196565f82ed51220f",
    "ASSISTANT_ID": "asst_AAbf5acxGSYy6NpApw2oqiZg"
}

# --- PAGE SETUP ---
st.set_page_config(page_title="🏈 NFHS Football Rules Assistant – 2025 Edition", layout="wide")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition")

# --- HIDDEN DIGITAL WATERMARK (C, once) ---
st.markdown(
    """
    <style>
      /* Keep it in the DOM but off-screen; still copyable/detectable */
      .visually-hidden-watermark {
        position: absolute;
        left: -10000px;
        top: auto;
        width: 1px;
        height: 1px;
        overflow: hidden;
      }
    </style>
    <div class="visually-hidden-watermark">
      © 2025 Tommy Smith — NFHS Football Rules Assistant. Proprietary content and methods.
    </div>
    """,
    unsafe_allow_html=True
)

# --- WATERMARK (B, per-output helper) ---
def render_output_with_watermark(content: str) -> None:
    # Render the content (markdown/html) then add a subtle copyright line
    st.markdown(content, unsafe_allow_html=True)
    st.markdown(
        "<div style='margin-top:8px'><sub>© 2025 Tommy Smith — NFHS Football Rules Assistant</sub></div>",
        unsafe_allow_html=True
    )

# --- RULE LOOKUP FUNCTION ---
def ask_rule_lookup(rule_id: str) -> str | None:
    try:
        res = client.responses.create(
            prompt={"id": CONFIG["RULE_PROMPT_ID"], "version": "38"},
            input=[
                {
                    "role": "user",
                    "content": f"id:{rule_id}"
                }
            ],
            tools=[{
                "type": "file_search",
                "vector_store_ids": [CONFIG["VECTOR_STORE_ID"]]
            }],
            text={"format": {"type": "text"}},
            max_output_tokens=2048,
            store=True
        )

        # Scan the output for assistant-generated response
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

# --- GENERAL Q&A WITH TRACING ENABLED ---
async def _qa_agent_call(prompt: str, group_id: str | None = None) -> str:
    agent = Agent(name="Rules QA Assistant", instructions="Answer NFHS football rules questions.")
    with trace(workflow_name="NFHS_QA", group_id=group_id or None):
        result = await Runner.run(agent, prompt)
    return result.final_output

def ask_general(prompt: str) -> str | None:
    try:
        group_id = st.session_state.qa_thread_id or "default-thread"
        return asyncio.run(_qa_agent_call(prompt, group_id))
    except Exception as e:
        st.error(f"❌ QA lookup failed: {e}")
        return None

# --- RULE LOOKUP UI ---
def render_rule_section():
    # Clear general Q&A state if rule input is used
    if st.session_state.get("rule_input"):
        for key in ("qa_thread_id", "qa_last_prompt", "qa_last_reply"):
            st.session_state[key] = ""

    st.markdown("## 🔍 Search by Rule ID (e.g., 8-5-3d) or type a question/scenario")
    rule_input = st.text_input("Please your search here", key="rule_input")
    if st.button("Look Up", key="rule_button"):
        if rule_input.strip():
            result = ask_rule_lookup(rule_input.strip())
            st.session_state.rule_result = result
        else:
            st.warning("Please enter a rule ID to look up or Enter a question or scenario.")

    if st.session_state.get("rule_result"):
        st.markdown("### 📘 Rule Lookup Result")
        # Use per-output watermark (B)
        render_output_with_watermark(st.session_state.rule_result or "⚠️ No response.")

# --- GENERAL Q&A UI ---
def render_general_section() -> None:
    for key in ("qa_thread_id", "qa_last_prompt", "qa_last_reply"):
        st.session_state.setdefault(key, "")

    # Clear rule lookup state if general prompt is used
    if st.session_state.get("qa_prompt"):
        st.session_state["rule_input"] = ""
        st.session_state["rule_result"] = ""

    st.markdown("## 💬 Ask a Question About Rules or Scenarios")
    prompt = st.text_area("Enter a question or test-style scenario:",
                          placeholder="e.g., Can Team A recover their own punt after a muff?",
                          key="qa_prompt")

    if st.button("Ask", key="qa_button"):
        st.session_state.qa_last_prompt = prompt.strip()

    if st.session_state.qa_last_prompt:
        reply = ask_general(st.session_state.qa_last_prompt)
        st.session_state.qa_last_reply = reply or ""
        st.markdown("### 🧠 Assistant Reply")
        # Use per-output watermark (B)
        render_output_with_watermark(st.session_state.qa_last_reply or "⚠️ No response received.")

# --- MAIN ---
def main() -> None:
    render_rule_section()
    # Uncomment below if you want Q&A active
    # st.markdown("---")
    # render_general_section()

if __name__ == "__main__":
    main()

# --- FOOTER ---
st.markdown(
    """
    <style>
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        background-color: transparent;
        color: gray;
        text-align: center;
        font-size: 12px;
        padding: 5px;
        z-index: 9999;
    }
    </style>
    <div class="footer">
        NFHS Football Rules Assistant – 2025 Edition<br>
        © 2025 Tommy Smith. All Rights Reserved.
    </div>
    """,
    unsafe_allow_html=True
)
