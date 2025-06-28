import streamlit as st
import requests
import PyPDF2
from transformers import pipeline

# --- CONFIGURATION ---
st.set_page_config(page_title="LawAid - Best Legal AI", page_icon="⚖️", layout="wide")

# User input for Hugging Face API Key
hf_token = st.text_input("Enter your Hugging Face API Key", type="password")
if hf_token:
    st.session_state["HF_API_KEY"] = hf_token

HF_API_KEY = st.session_state.get("HF_API_KEY", "")  # Use user-provided key
PRIMARY_MODEL_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"  # Free public model
BACKUP_MODEL_URL = "https://api-inference.huggingface.co/models/distilbert-base-uncased"  # Backup free model
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}", "Content-Type": "application/json"}

# --- CHAT MEMORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- FUNCTIONS ---
def generate_response(prompt):
    if HF_API_KEY:
        payload = {"inputs": prompt}
        try:
            # Try primary model
            res = requests.post(PRIMARY_MODEL_URL, headers=HEADERS, json=payload, timeout=60)
            res.raise_for_status()
            output = res.json()
            if isinstance(output, list) and len(output) > 0:
                return output[0].get("generated_text", output[0].get("summary_text", "⚠️ Unexpected response format.")).strip()
            elif isinstance(output, dict):
                return output.get("generated_text", output.get("summary_text", "⚠️ Unexpected response format.")).strip()
            else:
                return "⚠️ Unexpected response format."
        except Exception as e:
            # Try backup model if primary fails
            try:
                res = requests.post(BACKUP_MODEL_URL, headers=HEADERS, json=payload, timeout=60)
                res.raise_for_status()
                output = res.json()
                if isinstance(output, list) and len(output) > 0:
                    return output[0].get("generated_text", output[0].get("summary_text", "⚠️ Unexpected response format (backup)." )).strip()
                elif isinstance(output, dict):
                    return output.get("generated_text", output.get("summary_text", "⚠️ Unexpected response format (backup)." )).strip()
                else:
                    return "⚠️ Unexpected response format (backup)."
            except Exception as e2:
                # Local fallback
                try:
                    local_pipe = pipeline("text-generation", model="gpt2")
                    result = local_pipe(prompt, max_length=100)
                    return result[0]['generated_text']
                except Exception as e3:
                    return f"⚠️ All models failed. Primary: {e}\nBackup: {e2}\nLocal: {e3}"
    else:
        # Local inference as fallback if no API key
        try:
            local_pipe = pipeline("text-generation", model="gpt2")
            result = local_pipe(prompt, max_length=100)
            return result[0]['generated_text']
        except Exception as e:
            return f"⚠️ Local model error: {e}"

def is_identity_question(text):
    text = text.lower()
    identity_keywords = [
        "who are you", "your name", "who created you", "who made you", "what is lawaid", "about lawaid", "who is your creator", "who developed you"
    ]
    return any(keyword in text for keyword in identity_keywords)

def is_greeting(text):
    greetings = ["hi", "hello", "hey", "namaste", "good morning", "good evening", "good afternoon"]
    return text.strip().lower() in greetings

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
if not HF_API_KEY:
    st.warning("Please enter your Hugging Face API Key above to use LawAid.")
else:
    user_input = st.chat_input("Ask your legal question or upload a file for analysis...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.spinner("LawAid is thinking..."):
            if is_greeting(user_input):
                reply = "Hello! I am LawAid, an open-source legal assistant web app powered by Hugging Face open models and Streamlit. How can I help you with Indian law today?"
            elif is_identity_question(user_input):
                reply = (
                    "I am the LawAid assistant, a legal AI created by GANNRAM DHRUV by integrating the Hugging Face assistant with this Streamlit app. "
                    "I provide general legal information about Indian law, powered by open-source models. For more, see the README or ask your question!"
                )
            else:
                reply = generate_response(user_input)
        st.session_state.messages.append({"role": "assistant", "content": f"```markdown\n{reply}\n```"})
        st.rerun()

# --- FILE UPLOAD ---
if HF_API_KEY:
    uploaded_file = st.file_uploader("Upload a case file (PDF or TXT)", type=["pdf", "txt"])
    if uploaded_file is not None:
        try:
            if uploaded_file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                file_text = "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
            else:
                file_text = uploaded_file.read().decode("utf-8")
            with st.spinner("Analyzing your case file..."):
                reply = generate_response(file_text)
            st.markdown(f"```markdown\n{reply}\n```")
        except Exception as e:
            st.error(f"Error reading file: {e}")

# --- DISCLAIMER ---
st.markdown("---")
st.caption("📜 LawAid is an AI-powered informational assistant. Not a substitute for licensed legal counsel.")
