import streamlit as st
from transformers import pipeline

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="TalentScout Hiring Assistant")

EXIT_KEYWORDS = {"exit", "quit", "stop", "end", "bye"}

# ==================================================
# LOAD PRE-TRAINED LLM (LOCAL, STABLE)
# ==================================================
@st.cache_resource
def load_llm():
    return pipeline(
        "text2text-generation",
        model="google/flan-t5-base",
        max_new_tokens=350,
        temperature=0.3
    )

llm = load_llm()

# ==================================================
# PROMPTS (CORE OF ASSIGNMENT)
# ==================================================

INFO_PROMPT = """
You are TalentScout’s Hiring Assistant.
Politely collect the required candidate information step by step.
Do not ask technical questions yet.
"""

QUESTION_PROMPT_TEMPLATE = """
You are a senior technical interviewer.

Generate {n} technical interview questions.

Rules:
- Questions must be based ONLY on the provided tech stack
- Each question must clearly mention at least one technology from the stack
- Scenario-based or problem-solving questions only
- No definitions
- No explanations
- No answers
- Each question on a new line

Candidate Experience: {experience} years
Tech Stack: {tech_stack}
"""

FALLBACK_MESSAGE = (
    "I’m sorry, I didn’t fully understand that. "
    "Please respond with the requested information so we can continue the screening."
)

# ==================================================
# SESSION STATE
# ==================================================
if "step" not in st.session_state:
    st.session_state.step = 0

if "candidate" not in st.session_state:
    st.session_state.candidate = {}

if "questions" not in st.session_state:
    st.session_state.questions = []

if "q_index" not in st.session_state:
    st.session_state.q_index = 0

if "last_input" not in st.session_state:
    st.session_state.last_input = None

# ==================================================
# UI
# ==================================================
st.title("🤖 TalentScout Hiring Assistant")
st.write(
    "Welcome to **TalentScout** 👋\n\n"
    "I’ll help with an initial screening by collecting your details "
    "and asking a few technical questions based on your tech stack."
)

user_input = st.chat_input("Type your response here...")

# ==================================================
# EXIT HANDLING
# ==================================================
if user_input and user_input.lower().strip() in EXIT_KEYWORDS:
    st.chat_message("assistant").write(
        "Thank you for your time! 🙏 Our recruitment team will review your profile and contact you soon."
    )
    st.stop()

# ==================================================
# INFORMATION GATHERING FLOW
# ==================================================
info_questions = [
    ("full_name", "What is your full name?"),
    ("email", "What is your email address?"),
    ("phone", "What is your phone number?"),
    ("experience", "How many years of professional experience do you have?"),
    ("position", "What position(s) are you applying for?"),
    ("location", "What is your current location?"),
    ("tech_stack", "Please list your tech stack (languages, frameworks, tools — comma separated)")
]

if st.session_state.step < len(info_questions):
    key, question_text = info_questions[st.session_state.step]
    st.chat_message("assistant").write(question_text)

    if user_input and user_input != st.session_state.last_input:
        st.session_state.last_input = user_input.strip()

        # Basic fallback for empty / nonsense input
        if not st.session_state.last_input:
            st.chat_message("assistant").write(FALLBACK_MESSAGE)
        else:
            st.session_state.candidate[key] = st.session_state.last_input
            st.session_state.step += 1

        st.rerun()

# ==================================================
# TECHNICAL QUESTION GENERATION
# ==================================================
elif st.session_state.step == len(info_questions):
    tech_stack = st.session_state.candidate["tech_stack"]
    experience = st.session_state.candidate["experience"]

    with st.spinner("Generating technical questions based on your tech stack..."):
        prompt = QUESTION_PROMPT_TEMPLATE.format(
            n=5,
            experience=experience,
            tech_stack=tech_stack
        )
        raw_output = llm(prompt)[0]["generated_text"]

    # Clean and normalize questions
    questions = []
    for line in raw_output.split("\n"):
        clean = line.strip().lstrip("0123456789.-•) ").strip()
        if len(clean) > 30:
            questions.append(clean)

    if len(questions) < 3:
        st.chat_message("assistant").write(
            "I had trouble generating clear technical questions. "
            "Please ensure your tech stack is specific (e.g., Python, Django, PostgreSQL)."
        )
        st.stop()

    st.session_state.questions = questions[:5]
    st.session_state.q_index = 0
    st.session_state.step += 1
    st.rerun()

# ==================================================
# ASK TECHNICAL QUESTIONS
# ==================================================
else:
    i = st.session_state.q_index
    questions = st.session_state.questions

    if i < len(questions):
        st.chat_message("assistant").write(questions[i])

        if user_input and user_input != st.session_state.last_input:
            st.session_state.last_input = user_input
            st.session_state.q_index += 1
            st.rerun()
    else:
        st.chat_message("assistant").write(
            "✅ Thank you for completing the initial screening!\n\n"
            "Our recruitment team will review your responses and get back to you with next steps."
        )
