import streamlit as st
import requests
from datetime import datetime

# --- CONFIG ---
PRIMARY_MODEL_URL = "https://api-inference.huggingface.co/models/google/gemma-7b-it"
FALLBACK_MODEL_URL = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"

# --- PAGE SETUP ---
st.set_page_config(
    page_title="LawAid India",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .main { background-color: #f5f5f5; }
    .stChatMessage { padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem; border: 1px solid #e0e0e0; }
    .stChatMessage[data-testid="stChatMessage"] { background-color: white; }
    .stChatInput { border-radius: 0.5rem; }
    .sidebar .sidebar-content { background-color: #ffffff; }
    .stButton button { width: 100%; border-radius: 0.5rem; padding: 0.5rem 1rem; background-color: #4CAF50; color: white; }
    .stButton button:hover { background-color: #45a049; }
    .stSlider { padding: 1rem 0; }
    .stMarkdown { padding: 1rem; }
    .error-message { color: #d32f2f; padding: 1rem; border-radius: 0.5rem; background-color: #ffebee; margin: 1rem 0; }
    .success-message { color: #2e7d32; padding: 1rem; border-radius: 0.5rem; background-color: #e8f5e9; margin: 1rem 0; }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "temperature" not in st.session_state:
    st.session_state.temperature = 0.7
if "max_tokens" not in st.session_state:
    st.session_state.max_tokens = 256
if "last_error" not in st.session_state:
    st.session_state.last_error = None
if "fallback_used" not in st.session_state:
    st.session_state.fallback_used = False

# --- API KEY ---
HF_API_KEY = st.secrets["HF_API_KEY"] if "HF_API_KEY" in st.secrets else None

def generate_response(prompt):
    if not HF_API_KEY:
        st.session_state.last_error = "API key not configured. Add it to .streamlit/secrets.toml as HF_API_KEY."
        return None
    headers = {"Authorization": f"Bearer {HF_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": st.session_state.max_tokens,
            "temperature": st.session_state.temperature,
            "top_p": 0.95,
            "repetition_penalty": 1.15
        }
    }
    # Try primary model
    try:
        response = requests.post(PRIMARY_MODEL_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        st.session_state.fallback_used = False
        return response.json()[0]["generated_text"]
    except Exception as e:
        # Try fallback model
        try:
            response = requests.post(FALLBACK_MODEL_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            st.session_state.fallback_used = True
            return response.json()[0]["generated_text"]
        except Exception as fallback_e:
            st.session_state.last_error = f"Primary model error: {str(e)}\nFallback model error: {str(fallback_e)}"
            return None

def format_message(message, role):
    timestamp = datetime.now().strftime("%H:%M")
    if role == "user":
        return f"👤 You ({timestamp}):\n{message}"
    else:
        return f"⚖️ Assistant ({timestamp}):\n{message}"

def main():
    st.title("⚖️ LawAid India")
    st.markdown("### Your AI Legal Assistant (Open Source)")

    # --- SIDEBAR ---
    with st.sidebar:
        st.header("⚙️ Model Configuration")
        st.session_state.temperature = st.slider(
            "Temperature", 0.1, 1.0, st.session_state.temperature, 0.1,
            help="Higher values = more creative, lower = more focused"
        )
        st.session_state.max_tokens = st.slider(
            "Max Tokens", 64, 512, st.session_state.max_tokens, 64,
            help="Maximum length of the generated response"
        )
        st.markdown("---")
        st.subheader("ℹ️ About")
        st.markdown("""
        This AI legal assistant is powered by open-source models:
        - **Primary:** google/gemma-7b-it (legal Q&A)
        - **Fallback:** HuggingFaceH4/zephyr-7b-beta (general)
        - 100% free and open
        
        **Note:** For general guidance only. For specific legal advice, consult a qualified lawyer.
        """)
        st.subheader("🔗 Quick Links")
        st.markdown("""
        - [NALSA](https://nalsa.gov.in/)
        - [India Code](https://www.indiacode.nic.in/)
        - [Supreme Court](https://main.sci.gov.in/)
        """)
        st.markdown("---")
        if st.button("🗑️ Clear Chat History", key="clear_chat"):
            st.session_state.messages = []
            st.session_state.last_error = None
            st.session_state.fallback_used = False
            st.rerun()
        if not HF_API_KEY:
            st.warning("⚠️ API key not configured. Add it to .streamlit/secrets.toml as HF_API_KEY.")
            api_key = st.text_input("🔑 Hugging Face API Key", type="password")
            if api_key:
                st.session_state.HF_API_KEY = api_key
                st.rerun()

    # --- MAIN CHAT ---
    chat_container = st.container()
    with chat_container:
        if st.session_state.last_error:
            st.markdown(f'<div class="error-message">⚠️ {st.session_state.last_error}</div>', unsafe_allow_html=True)
            st.code(str(st.session_state.last_error), language="text")
        if st.session_state.get("fallback_used"):
            st.markdown('<div class="success-message">ℹ️ The primary model was unavailable. Fallback to ZEPHYR-7B-BETA was used.</div>', unsafe_allow_html=True)
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(format_message(message["content"], message["role"]))
        if prompt := st.chat_input("Ask your legal question..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(format_message(prompt, "user"))
            with st.spinner("🤔 Thinking..."):
                response = generate_response(prompt)
                if response:
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    with st.chat_message("assistant"):
                        st.markdown(format_message(response, "assistant"))
                else:
                    st.error("Failed to generate response. Please try again.")

if __name__ == "__main__":
    main() 