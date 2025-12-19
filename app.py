import streamlit as st
from transformers import pipeline
import uuid

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(page_title="TalentScout Hiring Assistant")
EXIT_KEYWORDS = {"exit", "quit", "stop", "end", "bye"}

# -----------------------------
# MODEL LOADING (OPTIMIZED)
# -----------------------------
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

llm = load_llm()
sentiment_analyzer = load_sentiment()

# -----------------------------
# PROMPT (IMPROVED FOR LLaMA)
# -----------------------------
SYSTEM_PROMPT = """
You are TalentScout’s Hiring Assistant.

Generate 3–5 HIGH-QUALITY technical interview questions.

STRICT RULES:
- Questions MUST be scenario-based or failure-based
- Focus on trade-offs, edge cases, performance, scalability
- NO definitions
- NO "What is" questions
- NO answers
- Each question must be specific to the tech stack

If the tech stack is unclear, respond EXACTLY with:
LOW_CONFIDENCE
"""

# -----------------------------
# FALLBACK QUESTIONS
# -----------------------------
def fallback_questions(stack):
    data = {
        "python": [
            "How would you debug a memory leak in a long-running Python service?",
            "How do you design concurrency for Python APIs under high load?"
        ],
        "sql": [
            "How would you investigate a production query that suddenly becomes slow?"
        ],
        "docker": [
            "How would you reduce Docker image size without affecting runtime performance?"
        ]
    }
    result = []
    for t in stack:
        result.extend(data.get(t.lower(), []))
    return result[:5]

# -----------------------------
# SESSION STATE
# -----------------------------
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "step" not in st.session_state:
    st.session_state.step = 0

if "candidate" not in st.session_state:
    st.session_state.candidate = {}

# -----------------------------
# UI
# -----------------------------
st.title("🤖 TalentScout Hiring Assistant")

st.write(
    "Hello 👋 I’ll guide you through an initial screening and ask a few "
    "technical questions based on your tech stack."
)

user_input = st.chat_input("Type your response here...")

# -----------------------------
# EXIT HANDLING
# -----------------------------
if user_input and user_input.lower().strip() in EXIT_KEYWORDS:
    st.chat_message("assistant").write(
        "Thank you for your time! Our recruitment team will contact you soon. 👋"
    )
    st.stop()

# -----------------------------
# STEP-BY-STEP SCRIPT
# -----------------------------
questions = [
    "What is your full name?",
    "What is your email address?",
    "How many years of experience do you have?",
    "What position are you applying for?",
    "What is your current location?",
    "Please list your tech stack (comma separated)"
]

if st.session_state.step < len(questions):
    st.chat_message("assistant").write(questions[st.session_state.step])

    if user_input:
        st.session_state.candidate[questions[st.session_state.step]] = user_input
        st.session_state.step += 1
        st.rerun()

# -----------------------------
# TECHNICAL QUESTION GENERATION
# -----------------------------
elif st.session_state.step == len(questions):
    tech_stack = [
        t.strip() for t in
        st.session_state.candidate[questions[-1]].split(",")
        if t.strip()
    ]

    with st.spinner("Generating advanced technical questions..."):
        try:
            output = llm(prompt, return_full_text=False)[0]["generated_text"]
        except Exception as e:
            st.error("Model failed to generate questions. Using fallback.")
            output = "LOW_CONFIDENCE" 
        prompt = f"""
{SYSTEM_PROMPT}

Candidate Experience: {st.session_state.candidate[questions[2]]}
Tech Stack: {", ".join(tech_stack)}
"""
            

    if output.strip() == "LOW_CONFIDENCE":
        tech_questions = fallback_questions(tech_stack)
    else:
        tech_questions = [
            q.strip()
            for q in output.split("\n")
            if "?" in q and len(q) > 20
        ][:5]

    st.session_state.tech_questions = tech_questions
    st.session_state.q_index = 0
    st.session_state.step += 1
    st.rerun()

# -----------------------------
# ASK TECH QUESTIONS + SENTIMENT
# -----------------------------
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
            "Our team will review your responses and reach out soon."
        )
