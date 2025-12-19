# TalentScout: AI Hiring Assistant 🤖

## I. Project Overview
TalentScout is an intelligent recruitment chatbot built with Python and Streamlit. It leverages the Llama 3.3 Large Language Model (via Groq Cloud) to automate the initial screening of technology candidates. The assistant gathers essential PII (Personally Identifiable Information), generates dynamic technical questions based on the candidate's specific tech stack, and provides a structured Excel report for recruiters.

## II. Technical Specifications
- **Frontend:** Streamlit (v1.30+)
- **LLM Provider:** Groq Cloud API
- **Model:** Llama-3.3-70b-versatile
- **Data Handling:** Pandas & XlsxWriter
- **Security:** Streamlit Secrets Management

## III. Prompt Engineering Design
The chatbot utilizes a multi-phase prompting strategy:
1. **System Persona:** Defines the bot as a professional recruiter, ensuring it stays on-topic and handles fallbacks gracefully.
2. **Dynamic Generation:** Once the 'Tech Stack' is identified, a specific prompt instructs the LLM to generate exactly 5 technical questions, filtering out introductory text to maintain a clean UI.
3. **Sequential State Management:** Using Streamlit's `session_state`, the bot tracks `info_step` and `tech_step` to ensure a one-question-at-a-time interaction.

## IV. Installation & Usage
1. **Clone:** `git clone <repository-url>`
2. **Install:** `pip install -r requirements.txt`
3. **Configure:** Create `.streamlit/secrets.toml` and add `GROQ_API_KEY = "your_key"`.
4. **Run:** `streamlit run app.py`

## V. Challenges & Solutions
- **Challenge:** Statelessness of LLMs. 
- **Solution:** Implemented a state machine using `st.session_state` to store candidate answers and track progress.
- **Challenge:** Data Export. 
- **Solution:** Integrated `BytesIO` with `pandas` to allow real-time generation of Excel files without saving local temporary files.
