import streamlit as st
from transformers import pipeline
import uuid

st.set_page_config(page_title="TalentScout Hiring Assistant")

@st.cache_resource
def load_model():
    return pipeline(
        "text-generation",
        model="meta-llama/Llama-3.2-1B",
        max_new_tokens=300,
        temperature=0.6
    )

llm = load_model()

SYSTEM_PROMPT = """
You are TalentScout’s Hiring Assistant.

Generate 3–5 advanced technical interview questions.
Rules:
- Scenario-based questions only
- No definitions or basic theory
- Do NOT provide answers
- Questions must match the provided tech stack

If unclear, respond exactly:
LOW_CONFIDENCE
"""

st.title("🤖 TalentScout Hiring Assistant")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

st.write("Welcome! I’ll help with an initial technical screening.")

experience = st.selectbox("Years of experience", ["1-3", "3-5", "5+"])
tech = st.text_input("Enter your tech stack (comma separated)")

def fallback(stack):
    data = {
        "python": [
            "How would you debug memory leaks in a Python service?",
            "How do you handle concurrency in Python APIs?"
        ],
        "sql": [
            "How would you optimize slow production queries?"
        ],
        "docker": [
            "How do you reduce Docker image size without performance loss?"
        ]
    }
    result = []
    for t in stack:
        result.extend(data.get(t.lower(), []))
    return result[:5]

if st.button("Generate Questions"):
    stack = [t.strip() for t in tech.split(",") if t.strip()]

    with st.spinner("Generating technical questions..."):
        prompt = f"""
{SYSTEM_PROMPT}

Candidate Experience: {experience}
Tech Stack: {", ".join(stack)}
"""
        output = llm(prompt)[0]["generated_text"]

    if output.strip() == "LOW_CONFIDENCE":
        questions = fallback(stack)
    else:
        questions = [q for q in output.split("\n") if q.strip()][:5]

    for q in questions:
        st.chat_message("assistant").markdown(f"• {q}")
