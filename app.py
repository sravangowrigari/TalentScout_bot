import streamlit as st
import pandas as pd
from io import BytesIO
from groq import Groq

# --- CONFIGURATION ---
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("🔑 API Key not found. Please set GROQ_API_KEY in Streamlit Secrets.")
    st.stop()

REQUIRED_INFO = [
    "Full Name", "Email Address", "Phone Number", 
    "Years of Experience", "Desired Position", "Current Location", "Tech Stack"
]

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.info_step = 0
    st.session_state.tech_questions = []
    st.session_state.tech_step = 0
    st.session_state.collected_data = {}
    st.session_state.messages.append({"role": "assistant", "content": "👋 Welcome! What is your **Full Name**?"})

# --- UI ---
st.set_page_config(page_title="TalentScout AI", page_icon="💼")
st.title("💼 TalentScout Interactive Assistant")

# Progress Bar
progress_pct = min(st.session_state.info_step / len(REQUIRED_INFO), 1.0)
st.progress(progress_pct, text=f"Profile Completion: {int(progress_pct*100)}%")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- CHAT LOGIC ---
if prompt := st.chat_input("Type here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").markdown(prompt)

    with st.chat_message("assistant"):
        # PHASE 1: Info Gathering
        if st.session_state.info_step < len(REQUIRED_INFO):
            field = REQUIRED_INFO[st.session_state.info_step]
            st.session_state.collected_data[field] = prompt
            st.session_state.info_step += 1
            
            if st.session_state.info_step < len(REQUIRED_INFO):
                response = f"Got it. What is your **{REQUIRED_INFO[st.session_state.info_step]}**?"
            else:
                st.balloons()
                with st.spinner("✨ Generating technical questions..."):
                    stack = st.session_state.collected_data["Tech Stack"]
                    res = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[{"role": "system", "content": f"Generate 5 interview questions for {stack}. Separated by newlines."}]
                    )
                    st.session_state.tech_questions = [q.strip() for q in res.choices[0].message.content.split('\n') if q.strip()][:5]
                    response = f"Great! Question 1: {st.session_state.tech_questions[0]}"
        
        # PHASE 2: Technical Questions
        elif st.session_state.tech_step < len(st.session_state.tech_questions) - 1:
            st.session_state.tech_step += 1
            idx = st.session_state.tech_step
            response = f"Acknowledge. Question {idx+1}: {st.session_state.tech_questions[idx]}"
        
        # PHASE 3: Excel Generation & Closing
        else:
            response = "🎉 All done! Recruiter report generated. Download it below."
            st.markdown(response)

            # --- EXCEL CREATION ---
            # Create a DataFrame for Profile
            profile_df = pd.DataFrame([st.session_state.collected_data])
            
            # Create a DataFrame for Chat History
            chat_data = [{"Role": m["role"], "Content": m["content"]} for m in st.session_state.messages]
            chat_df = pd.DataFrame(chat_data)

            # Save to BytesIO buffer
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                profile_df.to_excel(writer, sheet_name='Candidate_Profile', index=False)
                chat_df.to_excel(writer, sheet_name='Interview_Log', index=False)
            
            processed_data = output.getvalue()

            st.download_button(
                label="📊 Download Recruiter Report (Excel)",
                data=processed_data,
                file_name=f"TalentScout_{st.session_state.collected_data.get('Full Name', 'Candidate')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            st.session_state.messages.append({"role": "assistant", "content": response})
            st.stop()

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
