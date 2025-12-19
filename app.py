import streamlit as st
from transformers import pipeline

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="TalentScout Hiring Assistant")

EXIT_KEYWORDS = {"exit", "quit", "stop", "end", "bye"}

# --------------------------------------------------
# LOAD MODEL (BETTER QUALITY)
# --------------------------------------------------
@st.cache_resource
def load_llm():
    return pipeline(
        "text2text-generation",
        model="google/flan-t5-large",
        max_new_tokens=512,
        do_sample=False,          # deterministic
        num_beams=4               # forces multi-question output
    )

llm = load_llm()

# --------------------------------------------------
# STRONG TECH-STACK AWARE PROMPT
# --------------------------------------------------
SYSTEM_PROMPT = """
You are a senior technical interviewer.

TASK:
Generate 5 advanced technical interview questions.

STRICT REQUIREMENTS:
- Each question MUST explicitly reference at least one item from the tech stack
- Questions must be scenario-based or problem-solving
- Focus on real-world issues: performance, scalability, failures, trade-offs
- NO definitions
- NO theoretical explanations
- NO answers

FORMAT (MANDATORY):
Q1: <question>
Q2: <question>
Q3: <question>
Q4: <question>
Q5: <question>
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
    "Please list your tech stack (comma separated, e.g., Python, SQL, Docker)"
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
# TECH-STACK-SPECIFIC QUESTION GENERATION
# --------------------------------------------------
elif st.session_state.step == len(info_questions):
    tech_stack_raw = st.session_state.candidate[info_questions[-1]]
    tech_stack = [t.strip() for t in tech_stack_raw.split(",") if t.strip()]
    experience = st.session_state.candidate[info_questions[2]]

    with st.spinner("Generating advanced, tech-specific questions..."):
        prompt = f"""
{SYSTEM_PROMPT}

Candidate Experience: {experience} years
Tech Stack: {", ".join(tech_stack)}

IMPORTANT:
- Each question must clearly mention a technology from the stack
- Use real engineering scenarios
"""
        output = llm(prompt)[0]["generated_text"]

    # -------------------------------
    # ROBUST EXTRACTION (Q1–Q5)
    # -------------------------------
    questions = []
    for line in output.split("\n"):
        line = line.strip()
        if line.startswith("Q"):
            clean = line.split(":", 1)[-1].strip()
            if len(clean) > 40:
                questions.append(clean)

    # Safety net: keep only meaningful questions
    questions = questions[:5]

    if len(questions) < 3:
        st.error(
            "The AI response was not detailed enough. "
            "Please provide a clearer tech stack (e.g., Python, SQL, Docker, AWS)."
        )
        st.stop()

    st.session_state.tech_questions = questions
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
