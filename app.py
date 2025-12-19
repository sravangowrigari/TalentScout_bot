import streamlit as st
import uuid
import os
import time
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
# SENTIMENT (EXPLICIT MODEL)
# --------------------------------------------------
@st.cache_resource
def load_sentiment():
    return pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english"
    )

sentiment_analyzer = load_sentiment()

# --------------------------------------------------
# PROMPT (STRICT)
# --------------------------------------------------
SYSTEM_PROMPT = """
You are a senior technical interviewer.

Generate ONLY technical interview questions.

MANDATORY FORMAT:
- Generate 3 to 5 questions
- One question per line
- Each question must end with '?'
- Output ONLY the questions

CONTENT RULES:
- Scenario-based or failure-based
- Focus on scalability, performance, trade-offs, edge cases
- No definitions
- No explanations
- No answers
"""

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
# MODEL-ONLY QUESTION GENERATION (WITH RETRY)
# --------------------------------------------------
elif st.session_state.step == len(info_questions):
    tech_stack = st.session_state.candidate[info_questions[-1]]

    payload = {
        "inputs": (
            f"{SYSTEM_PROMPT}\n"
            f"Tech Stack: {tech_stack}\n"
            f"IMPORTANT: Follow the format strictly."
        ),
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.4,
            "return_full_text": False
        }
    }

    max_retries = 5
    wait_seconds = 10
    raw_text = None

    with st.spinner("Warming up AI model and generating questions..."):
        for attempt in range(max_retries):
            response = requests.post(
                HF_API_URL,
                headers=HEADERS,
                json=payload,
                timeout=60
            )

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and "generated_text" in data[0]:
                    raw_text = data[0]["generated_text"]
                    if raw_text.strip():
                        break

            time.sleep(wait_seconds)

    if not raw_text:
        st.error(
            "The AI model did not become ready in time. "
            "Please try again in a minute."
        )
        st.stop()

    model_questions = [
        q.strip()
        for q in raw_text.split("\n")
        if q.strip().endswith("?")
    ]

    if len(model_questions) < 3:
        st.error(
            "The AI model responded, but did not generate valid interview questions. "
            "Please refine the tech stack and try again."
        )
        st.stop()

    st.session_state.tech_questions = model_questions[:5]
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
