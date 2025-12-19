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
    "google/flan-t5-base"
)

HEADERS = {
    "Authorization": f"Bearer {HF_API_TOKEN}",
    "Content-Type": "application/json"
}

# --------------------------------------------------
# SENTIMENT (OPTIONAL, EXPLICIT MODEL)
# --------------------------------------------------
@st.cache_resource
def load_sentiment():
    return pipeline(
        "sentiment-analysis",
        model="distilbert-base-uncased-finetuned-sst-2-english"
    )

sentiment_analyzer = load_sentiment()

# --------------------------------------------------
# PROMPT (FLAN-T5 OPTIMIZED)
# --------------------------------------------------
SYSTEM_PROMPT = """
Generate 3 to 5 advanced technical interview questions.

Rules:
- One question per line
- Each must end with '?'
- Scenario-based or failure-based only
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
# MODEL-ONLY QUESTION GENERATION (FLAN-T5)
# --------------------------------------------------
elif st.session_state.step == len(info_questions):
    tech_stack = st.session_state.candidate[info_questions[-1]]

    with st.spinner("Generating technical questions..."):
        payload = {
            "inputs": f"{SYSTEM_PROMPT}\nTech Stack: {tech_stack}",
            "parameters": {
                "max_new_tokens": 200
            }
        }

        response = requests.post(
            HF_API_URL,
            headers=HEADERS,
            json=payload,
            timeout=30
        )

    if response.status_code != 200:
        st.error("AI model request failed. Please try again.")
        st.stop()

    data = response.json()

    if not isinstance(data, list) or "generated_text" not in data[0]:
        st.error("AI model returned invalid output.")
        st.stop()

    raw_text = data[0]["generated_text"]

    model_questions = [
        q.strip()
        for q in raw_text.split("\n")
        if q.strip().endswith("?")
    ]

    if len(model_questions) < 3:
        st.error(
            "The AI model could not generate valid interview questions. "
            "Please refine the tech stack."
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
