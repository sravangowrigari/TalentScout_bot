import streamlit as st
from groq import Groq
import time

# --- SECURE CONFIGURATION ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("🔑 API Key not found. Please set GROQ_API_KEY in Streamlit Secrets.")
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
    st.session_state.tech_questions = []
    st.session_state.tech_step = 0
    st.session_state.collected_data = {}
    
    # Warm Opening
    opening = (
        "👋 **Hi there! I'm the TalentScout Assistant.**\n\n"
        "I'm thrilled to help you start your journey with us. I'll ask a few quick questions "
        "to get to know you, followed by a short technical chat. \n\n"
        "To get the ball rolling, what's your **Full Name**?"
    )
    st.session_state.messages.append({"role": "assistant", "content": opening})

# --- UI SETUP ---
st.set_page_config(page_title="TalentScout Assistant", page_icon="💼", layout="centered")
st.title("🚀 TalentScout Hiring Assistant Chatbot")

# Progress Bar for User Info
progress_value = min(st.session_state.info_step / len(REQUIRED_INFO), 1.0)
st.progress(progress_value, text=f"Profile Completion: {int(progress_value*100)}%")

# Display Chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- CHAT LOGIC ---
if prompt := st.chat_input("Type your message..."):
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
                # Personalized follow-up
                if field == "Full Name":
                    response = f"Nice to meet you, **{prompt}**! 😊 Next, could you share your **Email Address**?"
                elif field == "Desired Position":
                    response = f"That sounds like an exciting role! And where are you currently **located**?"
                else:
                    response = f"Got it. Thanks! Now, what is your **{next_f}**?"
            else:
                # TRANSITION: Intro to Tech Questions
                st.write("---")
                st.success("✅ Profile Complete! Now, let's dive into some technical fun.")
                with st.spinner("🧠 Analyzing your stack to find the perfect questions..."):
                    stack = st.session_state.collected_data["Tech Stack"]
                    sys_prompt = f"Generate 5 technical interview questions for a {stack} developer. Return only the questions separated by newlines."
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": sys_prompt}])
                    st.session_state.tech_questions = [q.strip() for q in res.choices[0].message.content.split('\n') if q.strip()][:5]
                    response = f"Ready? Let's go! 🚀\n\n**Question 1:** {st.session_state.tech_questions[0]}"
        
        # PHASE 2: Technical Questions
        elif st.session_state.tech_step < len(st.session_state.tech_questions) - 1:
            st.session_state.tech_step += 1
            idx = st.session_state.tech_step
            feedback = ["Great answer!", "Interesting insight!", "I like that approach.", "Clear and concise!"]
            response = f"{feedback[idx % len(feedback)]} \n\n**Question {idx+1}:** {st.session_state.tech_questions[idx]}"
        
        # PHASE 3: Interactive Closing
        else:
            response = (
                "🎉 **We're all set!**\n\n"
                "Thank you so much for your time today. I've sent your profile and responses "
                "to our hiring managers. You should hear from a human member of our team "
                "within **2-3 business days** via email.\n\n"
                "Have a fantastic day ahead! ✨"
            )
            
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
