# TalentScout Hiring Assistant 🤖

TalentScout is an intelligent recruitment chatbot designed to streamline the initial screening process. It gathers candidate information and generates tailored technical questions based on the candidate's tech stack.

## ✨ Features
- **Sequential Information Gathering**: Collects name, contact info, and experience step-by-step.
- **Dynamic Technical Screening**: Generates 3-5 specific questions using Llama 3 based on the candidate's stack.
- **Secure Integration**: Uses Streamlit Secrets to manage API keys safely.

## 🚀 Installation & Local Setup
1. Clone this repository: `git clone <your-repo-link>`
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your API key: 
   - Create a folder `.streamlit`
   - Create a file `secrets.toml` inside it
   - Add: `GROQ_API_KEY = "your_key_here"`
4. Run the app: `streamlit run app.py`

## 🛠️ Tech Stack
- **Frontend**: Streamlit
- **LLM**: Llama 3.3 (via Groq Cloud)
- **Language**: Python
