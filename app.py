import streamlit as st
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
# PROMPT
# --------------------------------------------------
SYSTEM_PROMPT = """
Generate 4 technical interview questions.

Rules:
- Technical, scenario-based or problem-solving
- Related to the given tech stack
- No definitions, no explanations, no answers
- Return each question on a new line
"""

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "step" not in st.session_state:
    st.session_state.step = 0
if "candidate" not in st.session_state:
    st.session_state.candidate = {}
if "q_index" not in st.session_state:
    st.session_state.q_index = 0
if "tech_questions" not in st.session_state:
    st.session_state.tech_questions = []
if "last_input" not in st.session_state:
    st.session_state.last_input = None

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

    if user_input and user_input != st.session_state.last_input:
        st.session_state.last_input = user_input
        st.session_state.candidate[
            info_questions[st.session_state.step]
        ] = user_input
        st.session_state.step += 1
        st.rerun()

# --------------------------------------------------
# MODEL QUESTION GENERATION
# --------------------------------------------------
elif st.session_state.step == len(info_questions):
    tech_stack = st.session_state.candidate[info_questions[-1]]

    with st.spinner("Generating technical questions..."):
        prompt = f"{SYSTEM_PROMPT}\nTech Stack: {tech_stack}"
        raw_output = llm(prompt)[0]["generated_text"]

    # Robust, tolerant extraction (no strict formatting assumptions)
    lines = [l.strip() for l in raw_output.split("\n")]
    questions = []
    for l in lines:
        l = l.lstrip("0123456789.-•) ").strip()
        if len(l) >= 25:
            questions.append(l)

    if not questions:
        questions = [raw_output.strip()]

    st.session_state.tech_questions = questions[:4]
    st.session_state.q_index = 0
    st.session_state.step += 1
    st.rerun()

# --------------------------------------------------
# ASK TECH QUESTIONS
# --------------------------------------------------
else:
    qs = st.session_state.tech_questions
    i = st.session_state.q_index

    if i < len(qs):
        st.chat_message("assistant").write(qs[i])

        if user_input and user_input != st.session_state.last_input:
            st.session_state.last_input = user_input
            st.session_state.q_index += 1
            st.rerun()
    else:
        st.chat_message("assistant").write(
            "Thank you for completing the screening! "
            "Our recruitment team will review your responses."
        )
