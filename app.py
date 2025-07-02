import streamlit as st
st.set_page_config(page_title="LawAid - Best Legal AI", page_icon="⚖️", layout="wide")
import requests
import PyPDF2
from transformers import pipeline
import serpapi

# --- CUSTOM CSS FOR LEGAL-THEMED, BLACK BACKGROUND UI ---
legal_black_css = '''
<style>
body, .stApp {
    background: #101010 !important;
    color: #f5f5e6 !important;
    font-family: 'Georgia', 'Times New Roman', serif;
}
.stChatMessage.user, .stChatMessage.assistant {
    background: #181818 !important;
    color: #f5f5e6 !important;
    border-radius: 16px;
    margin-bottom: 16px;
    padding: 16px 18px 12px 18px;
    box-shadow: 0 2px 8px #0003;
    border: 1.5px solid #bfa14a;
    display: flex;
    align-items: flex-start;
    gap: 12px;
}
.stChatMessage .avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: #bfa14a;
    color: #101010;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3em;
    margin-top: 2px;
    border: 2px solid #fffbe6;
}
.stChatMessage .content {
    flex: 1;
    padding: 0;
    margin: 0;
}
.stChatMessage.assistant .content p {
    margin: 0 0 12px 0;
    line-height: 1.85;
    text-indent: 2em;
    color: #f5f5e6;
    font-size: 1.13em;
    background: none;
    border-radius: 0;
    padding: 0;
    font-family: 'Georgia', 'Times New Roman', serif;
}
.stChatMessage.user .content {
    color: #f5f5e6;
    font-weight: 600;
    font-size: 1.08em;
    font-family: 'Georgia', 'Times New Roman', serif;
}
.stChatMessage.assistant .content a {
    color: #ffd700;
    text-decoration: underline;
    font-size: 0.98em;
}
.header-credit {
    color: #ffd700;
    font-size: 0.93em;
    margin-left: 44px;
    margin-top: 2px;
    font-family: 'Georgia', 'Times New Roman', serif;
    letter-spacing: 0.2px;
}
</style>
'''
st.markdown(legal_black_css, unsafe_allow_html=True)

# --- UI HEADER ---
st.markdown("""
<div style='display: flex; flex-direction: column; align-items: flex-start; gap: 0; margin-bottom: 18px; margin-top: 18px;'>
    <div style='display: flex; align-items: center; gap: 12px;'>
        <span style='font-size:2em;color:#ffd700;'>⚖️</span>
        <div>
            <h2 style='margin-bottom:0;color:#ffd700;font-weight:700;font-family:Georgia,serif;'>LawAid: India's Legal Assistant</h2>
        </div>
    </div>
    <div class='header-credit'>Created by GANNARAM DHRUV</div>
</div>
""", unsafe_allow_html=True)

# --- CONFIGURATION ---

# User input for Hugging Face API Key
hf_token = st.text_input("Enter your Hugging Face API Key", type="password")
if hf_token:
    st.session_state["HF_API_KEY"] = hf_token

# Set default SerpAPI key
DEFAULT_SERPAPI_KEY = "6e8606d5bc89c6fc024d32291361455dcfd8a97ac3ad35db87f2ac6b871e3183"
SERPAPI_KEY = DEFAULT_SERPAPI_KEY

HF_API_KEY = st.session_state.get("HF_API_KEY", "")
PRIMARY_MODEL_URL = "https://api-inference.huggingface.co/models/deepset/legal-bert-base-uncased"  # Legal QA model
BACKUP_MODEL_URL = "https://api-inference.huggingface.co/models/distilbert-base-uncased"  # Backup free model
HEADERS = {"Authorization": f"Bearer {HF_API_KEY}", "Content-Type": "application/json"}

# --- CHAT MEMORY ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- FUNCTIONS ---
def legal_qa_from_text(question, context):
    """Use a legal-domain QA model to answer a question from context text. Always return a detailed paragraph."""
    if not HF_API_KEY:
        return None, None
    prompt = f"Answer the following legal question in a detailed paragraph, citing relevant law if possible.\nQuestion: {question}\nContext: {context}"
    payload = {
        "inputs": {
            "question": question,
            "context": context
        },
        "parameters": {"max_length": 512}
    }
    try:
        res = requests.post(PRIMARY_MODEL_URL, headers=HEADERS, json=payload, timeout=60)
        res.raise_for_status()
        output = res.json()
        if isinstance(output, dict) and "answer" in output:
            return output["answer"], None
        elif isinstance(output, list) and len(output) > 0 and "answer" in output[0]:
            return output[0]["answer"], None
        else:
            return None, None
    except Exception:
        return None, None

def legal_qa_from_pdf(question, pdf_text):
    """Try to answer a question from PDF text, splitting by page for citation."""
    pages = pdf_text.split("\f") if "\f" in pdf_text else pdf_text.split("\n\n")
    best_answer = None
    best_page = None
    for i, page in enumerate(pages):
        answer, _ = legal_qa_from_text(question, page)
        if answer and answer.strip() and answer.lower() not in ["", "no answer", "n/a"]:
            best_answer = answer
            best_page = i + 1
            break
    return best_answer, best_page

def serpapi_legal_search(query, serpapi_key):
    """Search the web for legal answers using SerpAPI and return a detailed multi-paragraph answer and link."""
    if not serpapi_key:
        return None, None
    params = {
        "engine": "google",
        "q": query + " site:gov.in OR site:indiankanoon.org OR site:barandbench.com OR site:consumeraffairs.nic.in OR site:indiacode.nic.in",
        "api_key": serpapi_key,
        "num": 8
    }
    try:
        results = serpapi.search(params)
        if "organic_results" in results and results["organic_results"]:
            snippets = []
            link = None
            for res in results["organic_results"][:8]:
                snippet = res.get("snippet") or res.get("description")
                if snippet:
                    snippets.append(snippet.strip())
                if not link and res.get("link"):
                    link = res.get("link")
            if snippets:
                # Join as paragraphs for a longer, richer answer
                paragraph = "\n\n".join(snippets)
                return paragraph, link
            else:
                return None, link
        else:
            return None, None
    except Exception:
        return None, None

def is_identity_question(text):
    text = text.lower()
    identity_keywords = [
        "who are you", "your name", "who created you", "who made you", "what is lawaid", "about lawaid", "who is your creator", "who developed you"
    ]
    return any(keyword in text for keyword in identity_keywords)

def is_greeting(text):
    greetings = ["hi", "hello", "hey", "namaste", "good morning", "good evening", "good afternoon"]
    return text.strip().lower() in greetings

# --- CLEAR CHAT ---
if st.button("🗑️ Reset Chat"):
    st.session_state.messages.clear()
    st.rerun()

# --- CHAT DISPLAY ---
for i in range(0, len(st.session_state.messages), 2):
    user_msg = st.session_state.messages[i]
    assistant_msg = st.session_state.messages[i+1] if i+1 < len(st.session_state.messages) else None
    st.markdown(f"""
    <div class='stChatMessage user'>
        <div class='avatar'>👤</div>
        <div class='content'><b>{user_msg['content']}</b></div>
    </div>
    """, unsafe_allow_html=True)
    if assistant_msg:
        st.markdown(f"""
        <div class='stChatMessage assistant'>
            <div class='avatar'>⚖️</div>
            <div class='content'>{assistant_msg['content']}</div>
        </div>
        """, unsafe_allow_html=True)

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
                uploaded_file = st.session_state.get("uploaded_file")
                pdf_answer, pdf_page = None, None
                if uploaded_file and uploaded_file.get("text"):
                    pdf_answer, pdf_page = legal_qa_from_pdf(user_input, uploaded_file["text"])
                if pdf_answer:
                    reply = f"<b>Answer from PDF (page {pdf_page}):</b><br><p style='margin-top:8px'>{pdf_answer}</p>"
                else:
                    web_answer, web_url = serpapi_legal_search(user_input, SERPAPI_KEY)
                    if web_answer:
                        reply = f"<b>Web-sourced answer:</b><br><p style='margin-top:8px'>{web_answer}</p>"
                        if web_url:
                            reply += f"<div style='margin-top:8px'><a href='{web_url}' target='_blank'>Source</a></div>"
                    else:
                        reply = "Sorry, I could not find an answer in the PDF or on the web."
        st.session_state.messages.append({"role": "assistant", "content": reply})
        st.rerun()

# --- FILE UPLOAD ---
if HF_API_KEY:
    uploaded_file = st.file_uploader("Upload a case file (PDF or TXT)", type=["pdf", "txt"])
    if uploaded_file is not None:
        try:
            if uploaded_file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                file_text = "\f".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
            else:
                file_text = uploaded_file.read().decode("utf-8")
            st.session_state["uploaded_file"] = {"text": file_text}
            st.success("File uploaded and processed. Now ask your legal question!")
        except Exception as e:
            st.error(f"Error reading file: {e}")

# --- DISCLAIMER ---
st.markdown("---")
st.caption("📜 LawAid is an AI-powered informational assistant. Not a substitute for licensed legal counsel.")
