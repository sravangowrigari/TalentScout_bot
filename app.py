import streamlit as st
from groq import Groq

# --- SECURE CONFIGURATION ---
# On Streamlit Cloud, this pulls from the "Secrets" dashboard
# Locally, you can set this up in a .streamlit/secrets.toml file
try:
    client = Groq(api_key=st.secrets["GROQ_API_KEY"])
except Exception:
    st.error("API Key not found. Please set GROQ_API_KEY in Streamlit Secrets.")
    st.stop()

# --- RECRUITMENT LOGIC ---
REQUIRED_INFO = [
    "Full Name",
    "Email Address",
    "Phone Number",
    "Years of Experience",
    "Desired Position",
    "Current Location",
    "Tech Stack (e.g., Python, React, SQL)"
]

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are 'TalentScout', a friendly technical recruiter. "
        "Your goal is to screen candidates professionally. "
        "Ask only one question at a time. Once the tech stack is provided, "
        "generate 3-5 technical questions. If the user says 'exit' or 'bye', "
        "end the chat gracefully."
    )
}

# --- INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = [SYSTEM_PROMPT]
    st.session_state.info_step = 0
    st.session_state.collected_data = {}
    st.session_state.messages.append({"role": "assistant", "content": "Welcome to TalentScout! I'm here to help with your application. To start, what is your **Full Name**?"})

# --- UI DISPLAY ---
st.set_page_config(page_title="TalentScout Assistant", page_icon="💼")
st.title("💼 TalentScout Hiring Assistant")

for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- CHAT INPUT ---
if prompt := st.chat_input("Enter your response here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Check for exit
    if any(stop in prompt.lower() for stop in ["exit", "quit", "bye"]):
        farewell = "Thank you for your time! Our team will review your profile. Goodbye!"
        st.chat_message("assistant").markdown(farewell)
        st.stop()

    # Generate Response
    with st.chat_message("assistant"):
        # Information Gathering Phase
        if st.session_state.info_step < len(REQUIRED_INFO):
            current_field = REQUIRED_INFO[st.session_state.info_step]
            st.session_state.collected_data[current_field] = prompt
            st.session_state.info_step += 1
            
            if st.session_state.info_step < len(REQUIRED_INFO):
                next_field = REQUIRED_INFO[st.session_state.info_step]
                response = f"Got it. Next, what is your **{next_field}**?"
            else:
                with st.spinner("Preparing your technical questions..."):
                    tech_context = f"Candidate has {st.session_state.collected_data['Years of Experience']} years experience. Tech stack: {st.session_state.collected_data['Tech Stack (e.g., Python, React, SQL)']}. Generate 3-5 relevant technical questions."
                    history = st.session_state.messages + [{"role": "system", "content": tech_context}]
                    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=history)
                    response = res.choices[0].message.content
        # Technical Interview Phase
        else:
            res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=st.session_state.messages)
            response = res.choices[0].message.content

        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
