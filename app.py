import streamlit as st
import requests

# --- CONFIGURATION ---
st.set_page_config(page_title="LawAid - Best Legal AI", page_icon="⚖️", layout="wide")

PRIMARY_MODEL_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
FALLBACK_MODEL_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.2"
HF_API_KEY = "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"

SYSTEM_PROMPT = (
    "You are LawAid, India's most trusted legal AI developed by Dhruvjoy. "
    "You must provide highly accurate, lawful, respectful answers based only on Indian law. "
    "Avoid hallucination. If unsure, say so. Do not offer personal opinions."
)

HEADERS = {"Authorization": f"Bearer {HF_API_KEY}", "Content-Type": "application/json"}

# --- CHAT MEMORY ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

# --- FUNCTIONS ---
def generate_response(messages):
    if not HF_API_KEY:
        return "❌ API key not set. Add `HF_API_KEY` in `.streamlit/secrets.toml`"

    payload = {
        "inputs": messages,
        "parameters": {
            "max_new_tokens": 512,
            "temperature": 0.2,
            "top_p": 0.9,
            "repetition_penalty": 1.15,
        }
    }

    # Try primary model first
    try:
        res = requests.post(PRIMARY_MODEL_URL, headers=HEADERS, json=payload, timeout=60)
        res.raise_for_status()
        return res.json()[0]["generated_text"].split("Assistant:")[-1].strip()
    except Exception as e:
        # Try fallback model
        try:
            res = requests.post(FALLBACK_MODEL_URL, headers=HEADERS, json=payload, timeout=60)
            res.raise_for_status()
            return res.json()[0]["generated_text"].split("Assistant:")[-1].strip() + "\n\n(Fallback model used: Mistral-7B-Instruct)"
        except Exception as fallback_e:
            return f"⚠️ Error: {e}\n⚠️ Fallback Error: {fallback_e}"

# --- UI HEADER ---
st.title("⚖️ LawAid: India's Legal Assistant (v2)")
st.markdown("Ask any legal question about Indian law. Answers are AI-generated and may not substitute for professional advice.")

# --- CLEAR CHAT ---
if st.button("🗑️ Reset Chat"):
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    st.rerun()

# --- CHAT DISPLAY ---
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").markdown(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").markdown(msg["content"])

# --- USER INPUT ---
user_input = st.chat_input("Ask your legal question...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("LawAid is thinking..."):
        full_prompt = "\n".join(
            [f"{m['role'].capitalize()}: {m['content']}" for m in st.session_state.messages if m["role"] != "system"]
        )
        full_prompt = f"{SYSTEM_PROMPT}\n\n{full_prompt}\nAssistant:"
        reply = generate_response(full_prompt)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

# --- DISCLAIMER ---
st.markdown("---")
st.caption("📜 LawAid is an AI-powered informational assistant. Not a substitute for licensed legal counsel.") 
