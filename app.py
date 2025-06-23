import streamlit as st
import requests
import PyPDF2

# --- CONFIGURATION ---
st.set_page_config(page_title="LawAid - Best Legal AI", page_icon="⚖️", layout="wide")

PRIMARY_MODEL_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
HF_API_KEY = "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"  # Updated Token

SYSTEM_PROMPT = (
    "You must provide highly accurate, lawful, respectful answers based only on Indian law. "
    "Avoid hallucination. If unsure, say so. Do not offer personal opinions."
)

HEADERS = {"Authorization": f"Bearer {HF_API_KEY}", "Content-Type": "application/json"}

# --- CHAT MEMORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- FUNCTIONS ---
def generate_response(prompt):
    if not HF_API_KEY:
        return "❌ API key not set. Please add it in `.streamlit/secrets.toml`."

    payload = {"inputs": prompt}

    try:
        res = requests.post(PRIMARY_MODEL_URL, headers=HEADERS, json=payload, timeout=60)
        res.raise_for_status()
        output = res.json()
        # Handle both list and dict responses
        if isinstance(output, list) and len(output) > 0:
            return output[0].get("generated_text", "⚠️ Unexpected response format.").strip()
        elif isinstance(output, dict):
            return output.get("generated_text", "⚠️ Unexpected response format.").strip()
        else:
            return "⚠️ Unexpected response format."
    except Exception as e:
        return f"⚠️ Error: {e}"

# --- UI HEADER ---
st.title("⚖️ LawAid: India's Legal Assistant (v2)")
st.markdown("Ask any legal question about Indian law. AI-generated answers may not substitute for professional advice.")

# --- CLEAR CHAT ---
if st.button("🗑️ Reset Chat"):
    st.session_state.messages.clear()
    st.rerun()

# --- CHAT DISPLAY ---
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.chat_message("user").markdown(msg["content"])
    elif msg["role"] == "assistant":
        st.chat_message("assistant").markdown(msg["content"])

# --- USER INPUT ---
user_input = st.chat_input("Ask your legal question or upload a file for analysis...")
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("LawAid is thinking..."):
        full_prompt = user_input
        reply = generate_response(full_prompt)
    st.session_state.messages.append({"role": "assistant", "content": f"```markdown\n{reply}\n```"})
    st.rerun()

# Add file uploader to the UI
uploaded_file = st.file_uploader("Upload a case file (PDF or TXT)", type=["pdf", "txt"])
if uploaded_file is not None:
    if uploaded_file.type == "application/pdf":
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        file_text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
    else:
        file_text = uploaded_file.read().decode("utf-8")
    with st.spinner("Analyzing your case file..."):
        reply = generate_response(file_text + "\n\nPlease provide detailed legal suggestions based on this case file.")
    st.markdown(f"```markdown\n{reply}\n```")

# --- DISCLAIMER ---
st.markdown("---")
st.caption("📜 LawAid is an AI-powered informational assistant. Not a substitute for licensed legal counsel.")
