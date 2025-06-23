# LawAid India – Open Source AI Legal Assistant

A modern, open-source legal assistant web app powered by Hugging Face open models and Streamlit.

## Features
- 100% Streamlit frontend (modern chat UI)
- Uses only open, public models (no paid access required)
- Sidebar for model config, info, and legal links
- Chat history, error handling, and clear feedback

## Models Used
- **Primary:** `HuggingFaceH4/zephyr-7b-beta`

## Setup
1. **Clone this repo:**
   ```bash
   git clone <your-repo-url>
   cd law_aid_app
   ```
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Add your Hugging Face API key:**
   - Create a file `.streamlit/secrets.toml` with:
     ```toml
     HF_API_KEY = "your_huggingface_api_key"
     ```
   - [Get your free API key here](https://huggingface.co/settings/tokens)

4. **Run the app:**
   ```bash
   streamlit run app.py
   ```

5. **Open in your browser:**
   - Go to the URL shown in your terminal (usually http://localhost:8501)

## Screenshots
![screenshot](screenshot.png)

## License
MIT

## Credits
- [Streamlit](https://streamlit.io/)
- [Hugging Face](https://huggingface.co/)
- [google/gemma-7b-it](https://huggingface.co/google/gemma-7b-it)
- [HuggingFaceH4/zephyr-7b-beta](https://huggingface.co/HuggingFaceH4/zephyr-7b-beta)

## Data Sources

The application uses information from:
- India Code (indiacode.nic.in)
- National Legal Services Authority (NALSA)
- State-specific legal resources
- Consumer Protection Act
- Right to Information Act

## Disclaimer

This application provides general legal information and guidance only. It is not a substitute for professional legal advice. For specific legal matters, please consult a qualified lawyer.

## Contributing

Contributions to improve the knowledge base or add new features are welcome. Please ensure all information is accurate and properly sourced. 
