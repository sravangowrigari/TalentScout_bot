import streamlit as st
import uuid
import os
import requests
from transformers import pipeline

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(page_title="TalentScout Hiring Assistant")

EXIT_KEYWORDS = {"exit", "quit", "stop", "end", "bye"}

HF_API_TOKEN = os.getenv("HF_API_TOKEN")
if not HF_API_TOKEN:
    st.error("HF_API_TOKEN not found. Add it in Streamlit Secrets.")
    st.stop()

HF_API_URL = (
    "https://api-inference.huggingface.co/models/"
    "mistralai/Mistral-7B-Instruct-v0.2"
)

HEADERS = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json"
}

# --------------------------------------------------
# SENTIMENT MODEL (EXPLICIT)
# --------------------------------------------------
@st.cache_resource
def load_sentiment():
    return pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english"
    )

sentiment_analyzer = load_sentiment()

# --------------------------------------------------
# PROMPT (MODEL-FRIENDLY)
# --------------------------------------------------
SYSTEM_PROMPT = """
You are a senior technical interviewer.

Generate technical interview questions ONLY.

Rules:
- Generate 3 to 5 questions
- One question per line
- Each question must end with '?'
- Scenario-based or failure-based
- Focus on scalability, performance, trade-offs, edge cases
- No definitions
- No explanations
- No answers
"""

# --------------------------------------------------
# FALLBACK QUESTIONS (HIGH QUALITY)
# --------------------------------------------------
def fallback_questions():
    return [
        "How would you debug a memory leak in a long-running production service?",
        "How do you design systems to handle sudden traffic spikes?",
        "How do you identify and resolve performance bottlenecks in production?",
        "How do you handle failures and retries in distributed systems?",
        "How would you design monitoring and alerting for a critical service?"
    ]

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "step" not in st.session_state:
    st.session_state.step = 0

if "candidate" not in st.session_state:
    st.session_state.candidate = {}

# --------------------------------------------------
# UI
# --------------------------------------------------
st.title("🤖 TalentScout Hiring Assistant")
st.write("Hello 👋 I’ll guide you through an initial technical screening.")

user_input = st.chat_input("Type your response here...")

# --------------------------------------------------
# EXIT HANDLING
# --------------------------------------------------
if user_input and user_input.lower().strip() in EXIT_KEYWORDS:
    st.chat_message("assistant").write(
        "Thank you for your time! Our recruitment team will contact you soon."
    )
    st.stop()

# --------------------------------------------------
# STEP-BY-STEP INFO COLLECTION
# --------------------------------------------------
info_questions = [
    "What is your full name?",
    "What is your email address?",
    "How many years of experience do you have?",
    "What position are you applying for?",
    "Please list your tech stack (comma separated)"
]

if st.session_state.step < len(info_questions):
    st.chat_message("assistant").write(info_questions[st.session_state.step])

    if user_input:
        st.session_state.candidate[
            info_questions[st.session_state.step]
        ] = user_input
        st.session_state.step += 1
        st.rerun()

# --------------------------------------------------
# QUESTION GENERATION (HF + HYBRID FALLBACK)
# --------------------------------------------------
elif st.session_state.step == len(info_questions):
    tech_stack = st.session_state.candidate[info_questions[-1]]

    with st.spinner("Generating technical questions..."):
        payload = {
            "inputs": (
                f"{SYSTEM_PROMPT}\n"
                f"Tech Stack: {tech_stack}\n"
                f"IMPORTANT: Output ONLY questions, one per line, ending with '?'"
            ),
            "parameters": {
                "max_new_tokens": 250,
                "temperature": 0.4,
                "return_full_text": False
            }
        }

        try:
            response = requests.post(
                HF_API_URL,
                headers=HEADERS,
                json=payload,
                timeout=60
            )
        except Exception:
            response = None

    model_questions = []

    if response and response.status_code == 200:
        data = response.json()

        # HF can return multiple formats
        if isinstance(data, list) and "generated_text" in data[0]:
            raw_text = data[0]["generated_text"]
        else:
            raw_text = ""

        model_questions = [
            q.strip()
            for q in raw_text.split("\n")
            if "?" in q
        ]

    # ---------------- HYBRID MODE ----------------
    final_questions = model_questions.copy()

    if len(final_questions) < 5:
        final_questions.extend(fallback_questions())

    final_questions = final_questions[:5]

    st.session_state.tech_questions = final_questions
    st.session_state.q_index = 0
    st.session_state.step += 1
    st.rerun()

# --------------------------------------------------
# ASK QUESTIONS + SENTIMENT
# --------------------------------------------------
else:
    i = st.session_state.q_index
    qs = st.session_state.tech_questions

    if i < len(qs):
        st.chat_message("assistant").write(qs[i])

        if user_input:
            sentiment = sentiment_analyzer(user_input)[0]
            st.chat_message("assistant").write(
                f"🧠 Detected sentiment: **{sentiment['label']}**"
            )
            st.session_state.q_index += 1
            st.rerun()
    else:
        st.chat_message("assistant").write(
            "Thank you for completing the screening! "
            "Our recruitment team will review your responses."
        )
