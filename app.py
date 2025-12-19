import streamlit as st
from transformers import pipeline
import uuid

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(page_title="TalentScout Hiring Assistant")

EXIT_KEYWORDS = {"exit", "quit", "stop", "end", "bye"}

# --------------------------------------------------
# MODEL LOADING (OPTIMIZED & CLOUD-SAFE)
# --------------------------------------------------
@st.cache_resource
def load_llm():
    return pipeline(
        "text-generation",
        model="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        max_new_tokens=200,
        temperature=0.5
    )

@st.cache_resource
def load_sentiment():
    return pipeline("sentiment-analysis")

st.info("⏳ Loading AI models (first load may take ~30 seconds)...")

llm = load_llm()
sentiment_analyzer = load_sentiment()

# --------------------------------------------------
# STRONG PROMPT (FIXED FOR SMALL LLMS)
# --------------------------------------------------
SYSTEM_PROMPT = """
You are a senior technical interviewer.

Generate exactly 3 to 5 technical interview questions.

FORMAT RULES:
- Each question must be on a new line
- Each question must end with a '?'
- No introductions
- No explanations
- No answers

CONTENT RULES:
- Scenario-based or failure-based questions only
- Focus on trade-offs, scalability, performance, edge cases
- No definitions
- No "What is" questions

If the tech stack is unclear, respond exactly:
LOW_CONFIDENCE
"""

# --------------------------------------------------
# FALLBACK QUESTIONS (GUARANTEED OUTPUT)
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
# UI HEADER
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
# STEP-BY-STEP CANDIDATE INFO SCRIPT
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
# TECHNICAL QUESTION GENERATION
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
        try:
            output = llm(prompt, return_full_text=False)[0]["generated_text"]
        except Exception:
            output = "LOW_CONFIDENCE"

    # 🔍 Robust parsing (FIXED)
    lines = [l.strip() for l in output.split("\n") if l.strip()]
    tech_questions = [l for l in lines if "?" in l]

    # Guaranteed fallback
    if len(tech_questions) < 3:
        tech_questions = fallback_questions(tech_stack)

    st.session_state.tech_questions = tech_questions
    st.session_state.q_index = 0
    st.session_state.step += 1
    st.rerun()

# --------------------------------------------------
# ASK TECH QUESTIONS + SENTIMENT ANALYSIS
# --------------------------------------------------
else:
    q_index = st.session_state.q_index
    tech_questions = st.session_state.tech_questions

    if q_index < len(tech_questions):
        st.chat_message("assistant").write(tech_questions[q_index])

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
