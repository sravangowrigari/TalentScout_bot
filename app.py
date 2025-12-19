import streamlit as st
import uuid
from transformers import pipeline

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="TalentScout Hiring Assistant")

EXIT_KEYWORDS = {"exit", "quit", "stop", "end", "bye"}

# --------------------------------------------------
# LOAD MODEL LOCALLY (ONCE)
# --------------------------------------------------
@st.cache_resource
def load_llm():
    return pipeline(
        "text2text-generation",
        model="google/flan-t5-base",
        max_new_tokens=200
    )

llm = load_llm()

# --------------------------------------------------
# PROMPT (FLAN-T5 FRIENDLY)
# --------------------------------------------------
SYSTEM_PROMPT = """
Generate 3 to 5 advanced technical interview questions.

Rules:
- One question per line
- Each question must end with '?'
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
# MODEL QUESTION GENERATION (LOCAL, RELIABLE)
# --------------------------------------------------
elif st.session_state.step == len(info_questions):
    tech_stack = st.session_state.candidate[info_questions[-1]]

    with st.spinner("Generating technical questions..."):
        prompt = f"""
{SYSTEM_PROMPT}
Tech Stack: {tech_stack}
"""
        output = llm(prompt)[0]["generated_text"]

    questions = [
        q.strip()
        for q in output.split("\n")
        if q.strip().endswith("?")
    ]

    if len(questions) < 3:
        st.error(
            "The AI model could not generate valid interview questions. "
            "Please refine the tech stack."
        )
        st.stop()

    st.session_state.tech_questions = questions[:5]
    st.session_state.q_index = 0
    st.session_state.step += 1
    st.rerun()

# --------------------------------------------------
# ASK QUESTIONS
# --------------------------------------------------
else:
    i = st.session_state.q_index
    qs = st.session_state.tech_questions

    if i < len(qs):
        st.chat_message("assistant").write(qs[i])

        if user_input:
            st.session_state.q_index += 1
            st.rerun()
    else:
        st.chat_message("assistant").write(
            "Thank you for completing the screening! "
            "Our recruitment team will review your responses."
        )
