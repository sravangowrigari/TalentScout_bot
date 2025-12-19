import streamlit as st
import uuid
import os
import google.generativeai as genai
from transformers import pipeline

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(page_title="TalentScout Hiring Assistant")
EXIT_KEYWORDS = {"exit", "quit", "stop", "end", "bye"}

# --------------------------------------------------
# GEMINI SETUP
# --------------------------------------------------
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-1.5-flash")

# --------------------------------------------------
# SENTIMENT (LIGHTWEIGHT)
# --------------------------------------------------
@st.cache_resource
def load_sentiment():
    return pipeline("sentiment-analysis")

sentiment_analyzer = load_sentiment()

# --------------------------------------------------
# PROMPT (GEMINI-OPTIMIZED)
# --------------------------------------------------
SYSTEM_PROMPT = """
You are TalentScout’s Hiring Assistant.

Generate 3 to 5 advanced technical interview questions.

STRICT RULES:
- Each question must be on a new line
- Each question must end with '?'
- Scenario-based or failure-based only
- Focus on performance, scalability, trade-offs, edge cases
- No definitions
- No answers
- No introductory text

If tech stack is unclear, respond exactly:
LOW_CONFIDENCE
"""

# --------------------------------------------------
# FALLBACK QUESTIONS
# --------------------------------------------------
def fallback_questions(stack):
    data = {
        "python": [
            "How would you debug a memory leak in a long-running Python service?",
            "How do you handle concurrency in Python APIs under high load?"
        ],
        "sql": [
            "How would you investigate and fix a slow production database query?"
        ],
        "docker": [
            "How would you reduce Docker image size without impacting runtime performance?"
        ]
    }
    result = []
    for t in stack:
        result.extend(data.get(t.lower(), []))
    return result[:5]

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "step" not in st.session_state:
    st.session_state.step = 0

if "candidate" not in st.session_state:
    st.session_state.candidate = {}

# --------------------------------------------------
# UI
# --------------------------------------------------
st.title("🤖 TalentScout Hiring Assistant")
st.write(
    "Hello 👋 I’ll guide you through an initial screening and ask a few "
    "technical questions based on your tech stack."
)

user_input = st.chat_input("Type your response here...")

# --------------------------------------------------
# EXIT HANDLING
# --------------------------------------------------
if user_input and user_input.lower().strip() in EXIT_KEYWORDS:
    st.chat_message("assistant").write(
        "Thank you for your time! Our recruitment team will contact you soon. 👋"
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
    "What is your current location?",
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
# TECH QUESTION GENERATION (GEMINI)
# --------------------------------------------------
elif st.session_state.step == len(info_questions):
    tech_stack = [
        t.strip()
        for t in st.session_state.candidate[
            info_questions[-1]
        ].split(",")
        if t.strip()
    ]

    with st.spinner("Generating advanced technical questions..."):
        prompt = f"""
{SYSTEM_PROMPT}

Candidate Experience: {st.session_state.candidate[info_questions[2]]}
Tech Stack: {", ".join(tech_stack)}
"""
        response = model.generate_content(prompt)
        output = response.text.strip()

    lines = [l.strip() for l in output.split("\n") if "?" in l]

    if len(lines) < 3:
        lines.extend(fallback_questions(tech_stack))

    st.session_state.tech_questions = lines[:5]
    st.session_state.q_index = 0
    st.session_state.step += 1
    st.rerun()

# --------------------------------------------------
# ASK QUESTIONS + SENTIMENT
# --------------------------------------------------
else:
    q_index = st.session_state.q_index
    questions = st.session_state.tech_questions

    if q_index < len(questions):
        st.chat_message("assistant").write(questions[q_index])

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
            "Our recruitment team will review your responses and get back to you."
        )
