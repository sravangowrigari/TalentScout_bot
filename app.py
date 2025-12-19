import streamlit as st
import pandas as pd
from io import BytesIO
from groq import Groq

# --- SECURE CONFIGURATION ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("🔑 API Key not found. Please set GROQ_API_KEY in Streamlit Secrets.")
    st.stop()

# --- RECRUITMENT PHASES ---
REQUIRED_INFO = [
    "Full Name", "Email Address", "Phone Number", 
    "Years of Experience", "Desired Position", "Current Location", "Tech Stack"
]

# --- SESSION STATE INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.info_step = 0
    st.session_state.tech_questions = []
    st.session_state.tech_step = 0
    st.session_state.collected_data = {}
    
    # Warm, Interactive Opening
    intro = (
        "👋 **Hi! I'm your TalentScout Hiring Partner.**\n\n"
        "I'm here to make your application process smooth and fun. We'll start with a "
        "quick profile setup, and then I'll challenge you with a few technical questions. "
        "Ready to start? \n\n**What is your full name?**"
    )
    st.session_state.messages.append({"role": "assistant", "content": intro})

# --- UI SETUP ---
st.set_page_config(page_title="TalentScout AI", page_icon="🚀", layout="centered")
st.title("🚀 TalentScout Interactive Portal")

# Interactive Progress Tracker
progress_pct = min(st.session_state.info_step / len(REQUIRED_INFO), 1.0)
st.progress(progress_pct, text=f"Application Progress: {int(progress_pct*100)}%")

# Display Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- CORE CHAT LOGIC ---
if prompt := st.chat_input("Type your message here..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    with st.chat_message("assistant"):
        # PHASE 1: Conversational Info Gathering
        if st.session_state.info_step < len(REQUIRED_INFO):
            field = REQUIRED_INFO[st.session_state.info_step]
            st.session_state.collected_data[field] = prompt
            st.session_state.info_step += 1
            
            if st.session_state.info_step < len(REQUIRED_INFO):
                next_f = REQUIRED_INFO[st.session_state.info_step]
                
                # Interactive "Human-like" transitions
                if field == "Full Name":
                    response = f"Nice to meet you, **{prompt}**! Let's get your contact info—what's your **Email Address**?"
                elif field == "Current Location":
                    response = f"**{prompt}** is a fantastic place! Lastly, what is your **Tech Stack** (e.g., Python, React, SQL)?"
                elif field == "Years of Experience":
                    response = f"**{prompt} years?** Impressive. What **Position** are you targeting today?"
                else:
                    response = f"Got it! Now, could you please provide your **{next_f}**?"
            else:
                # TRANSITION TO TECH QUESTIONS
                st.balloons()
                st.write("---")
                with st.status("✨ Creating your personalized interview...") as status:
                    st.write("Reviewing your tech stack...")
                    stack = st.session_state.collected_data["Tech Stack"]
                    st.write(f"Generating custom {stack} questions...")
                    
                    sys_prompt = f"Generate 5 interview questions for {stack}. Output ONLY the questions, separated by newlines."
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": sys_prompt}])
                    st.session_state.tech_questions = [q.strip() for q in res.choices[0].message.content.split('\n') if q.strip()][:5]
                    
                    status.update(label="Interview Ready!", state="complete", expanded=False)
                
                response = f"Great! Your profile is complete. Now for the fun part! 🧠\n\n**Question 1:** {st.session_state.tech_questions[0]}"
        
        # PHASE 2: Interactive Technical Interview
        elif st.session_state.tech_step < len(st.session_state.tech_questions) - 1:
            st.session_state.tech_step += 1
            idx = st.session_state.tech_step
            # Random encouraging feedback
            feedbacks = ["Excellent point!", "I like your thinking!", "Very clear explanation.", "Spot on!"]
            response = f"{feedbacks[idx % len(feedbacks)]} \n\n**Question {idx+1}:** {st.session_state.tech_questions[idx]}"
        
        # PHASE 3: Grand Finale & Excel Export
        else:
            response = (
                "🎉 **Amazing job! You've finished the screening.**\n\n"
                f"Thank you, {st.session_state.collected_data.get('Full Name')}. I've compiled your data into a "
                "Recruiter Report. You can download it below to keep for your records."
            )
            st.markdown(response)
            
            # Excel Logic
            profile_df = pd.DataFrame([st.session_state.collected_data])
            chat_df = pd.DataFrame([{"Role": m["role"], "Content": m["content"]} for m in st.session_state.messages])
            
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                profile_df.to_excel(writer, sheet_name='Candidate_Profile', index=False)
                chat_df.to_excel(writer, sheet_name='Full_Chat_History', index=False)
            
            st.download_button(
                label="📊 Download Final Recruiter Report (Excel)",
                data=output.getvalue(),
                file_name=f"TalentScout_{st.session_state.collected_data.get('Full Name')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.stop()

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
