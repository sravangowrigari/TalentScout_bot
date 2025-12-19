import streamlit as st
import os
import uuid
import google.generativeai as genai

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
st.set_page_config(page_title="TalentScout Hiring Assistant")

EXIT_KEYWORDS = {"exit", "quit", "stop", "end", "bye"}

# --------------------------------------------------
# GEMINI SETUP (STABLE)
# --------------------------------------------------
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    st.error("GEMINI_API_KEY not found in environment / Streamlit secrets")
    st.stop()

genai.configure(api_key=api_key)

# ✅ THIS MODEL NAME WORKS
model = genai.GenerativeModel("gemini-pro")

# --------------------------------------------------
# PROMPT
# --------------------------------------------------
SYSTEM_PROMPT = """
Generate 3 to 5 advanced technical interview questions.

Rules:
- One question per line
- Each line must end with '?'
- Scenario-based or failure-based only
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
        "Thank you for your time! Our recruitment team will contact you soon. 👋"
    )
    st.stop()

# --------------------------------------------------
# STEP-BY-STEP QUESTIONS
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
# GENERATE QUESTIONS (GEMINI)
# --------------------------------------------------
elif st.session_state.step == len(info_questions):
    tech_stack = st.session_state.candidate[info_questions[-1]]

    with st.spinner("Generating technical questions..."):
        response = model.generate_content(
            f"{SYSTEM_PROMPT}\nTech Stack: {tech_stack}"
        )
        output = response.text

    questions = [
        q.strip()
        for q in output.split("\n")
        if "?" in q
    ]

    if not questions:
        questions = [
            "How would you debug performance issues in a production system?",
            "How do you handle failures and retries in distributed systems?",
            "How do you design for scalability under unpredictable load?"
        ]

    st.session_state.tech_questions = questions
    st.session_state.q_index = 0
    st.session_state.step += 1
    st.rerun()

# --------------------------------------------------
# ASK TECH QUESTIONS
# --------------------------------------------------
else:
    q_index = st.session_state.q_index
    questions = st.session_state.tech_questions

    if q_index < len(questions):
        st.chat_message("assistant").write(questions[q_index])

        if user_input:
            st.session_state.q_index += 1
            st.rerun()
    else:
        st.chat_message("assistant").write(
            "Thank you for completing the screening!"
        )
