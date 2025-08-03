import time
import streamlit as st
from openai import OpenAI

# --- CONFIG ---
RULE_PROMPT_ID = "pmpt_688eb6bb5d2c8195ae17efd5323009e0010626afbd178ad9"
VS_VECTOR_STORE_ID = "vs_68883bb7d06881918ceeaa63a83f4725"
client = OpenAI(api_key=st.secrets["openai"]["api_key"])

# --- PAGE SETUP ---
st.set_page_config(page_title="🏈 NFHS Football Rules Assistant", layout="wide")
st.title("🏈 NFHS Football Rules Assistant – 2025 Edition")
st.caption("Ask a question or look up a rule. Built for players, coaches, and officials.")

# --- RULE LOOKUP FUNCTION ---
def ask_rule_lookup(rule_id: str) -> str | None:
    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # ✅ REQUIRED
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an NFHS football rules expert. The user is asking about a specific rule "
                        "from the 2025 rulebook. Search the attached vector store for entries where the metadata "
                        f"field `id` is exactly equal to `{rule_id}`. If found, use the `text` field as the rule’s definition. "
                        "Format your answer as:\n\n"
                        f"NFHS Rule {rule_id} defines the term or topic it addresses. Here is the rule:\n\n"
                        f"Rule {rule_id}: [insert rule text]\n\n"
                        "Further key points:\n- [clarifications or rulings]\n\n"
                        f"If `{rule_id}` is not found, respond: \"Rule {rule_id} was not found in the 2025 NFHS Rulebook.\""
                    )
                },
                {
                    "role": "user",
                    "content": f"What does rule {rule_id} say?"
                }
            ],
            tools=[
                {
                    "type": "file_search",
                    "vector_store_ids": [VS_VECTOR_STORE_ID]
                }
            ],
            tool_choice="auto",
            max_tokens=1024
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        st.error(f"❌ Rule lookup failed: {e}")
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

# --- MAIN ---
render_rule_section()
