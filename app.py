import streamlit as st
from groq import Groq

# --- SECURE CONFIGURATION ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("API Key not found. Please set GROQ_API_KEY in Streamlit Secrets.")
    st.stop()

# --- RECRUITMENT STEPS ---
REQUIRED_INFO = [
    "Full Name", "Email Address", "Phone Number", 
    "Years of Experience", "Desired Position", "Current Location", "Tech Stack"
]

# --- INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.info_step = 0
    st.session_state.tech_questions = [] # Stores the list of questions
    st.session_state.tech_step = 0      # Tracks which question we are on
    st.session_state.collected_data = {}
    
    # First greeting
    greeting = "Welcome to TalentScout! Let's start with your **Full Name**."
    st.session_state.messages.append({"role": "assistant", "content": greeting})

# --- UI SETUP ---
st.set_page_config(page_title="TalentScout Hiring Assistant", page_icon="💼")
st.title("💼 TalentScout Hiring Assistant")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- CHAT LOGIC ---
if prompt := st.chat_input("Enter your response..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    with st.chat_message("assistant"):
        # PHASE 1: Information Gathering
        if st.session_state.info_step < len(REQUIRED_INFO):
            field = REQUIRED_INFO[st.session_state.info_step]
            st.session_state.collected_data[field] = prompt
            st.session_state.info_step += 1
            
            if st.session_state.info_step < len(REQUIRED_INFO):
                next_f = REQUIRED_INFO[st.session_state.info_step]
                response = f"Got it. What is your **{next_f}**?"
            else:
                # TRANSITION: Generate Tech Questions
                with st.spinner("Generating technical questions based on your stack..."):
                    stack = st.session_state.collected_data["Tech Stack"]
                    sys_prompt = f"Generate exactly 5 technical interview questions for a candidate proficient in {stack}. Return only the questions separated by newlines, no intro text."
                    res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": sys_prompt}]
                    )
                    # Clean and split questions into a list
                    q_text = res.choices[0].message.content
                    st.session_state.tech_questions = [q.strip() for q in q_text.split('\n') if q.strip()][:5]
                    response = f"Great! Now I have some technical questions for you.\n\n**Question 1:** {st.session_state.tech_questions[0]}"
        
        # PHASE 2: One-by-One Technical Questions
        elif st.session_state.tech_step < len(st.session_state.tech_questions) - 1:
            st.session_state.tech_step += 1
            idx = st.session_state.tech_step
            response = f"Thank you. **Question {idx+1}:** {st.session_state.tech_questions[idx]}"
        
        # PHASE 3: Conclusion
        else:
            response = "Thank you for completing the screening! Our team will review your answers and contact you soon. Goodbye!"
            
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
