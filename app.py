import streamlit as st
import re
from transformers import pipeline

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="TalentScout Hiring Assistant")

EXIT_KEYWORDS = {"exit", "quit", "stop", "end", "bye"}

# --------------------------------------------------
# LOAD MODEL LOCALLY (CPU IS NORMAL)
# --------------------------------------------------
@st.cache_resource
def load_llm():
    return pipeline(
        "text2text-generation",
        model="google/flan-t5-base",
        max_new_tokens=300
    )

llm = load_llm()

# --------------------------------------------------
# PROMPT (FLAN-T5 OPTIMIZED)
# --------------------------------------------------
SYSTEM_PROMPT = """
Task: Generate interview questions.

Generate 4 technical interview questions.

Guidelines:
- Questions must be technical
- Scenario-based or problem-solving
- Related to the given tech stack
- Each question must end with a question mark

Format:
Return each question on a new line.
Do not include explanations or answers.
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
# MODEL QUESTION GENERATION (ROBUST)
# --------------------------------------------------
elif st.session_state.step == len(info_questions):
    tech_stack = st.session_state.candidate[info_questions[-1]]

    with st.spinner("Generating technical questions..."):
        prompt = f"""
{SYSTEM_PROMPT}

Tech Stack: {tech_stack}
"""
        output = llm(prompt)[0]["generated_text"]

    # Robust question extraction (FIX)
    questions = re.findall(r"[^?.!]*\?", output)
    questions = [q.strip() for q in questions]

    if len(questions) < 3:
        st.error(
            "The AI responded, but could not format usable interview questions. "
            "Please try a clearer tech stack (e.g., Python, SQL, Docker)."
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
