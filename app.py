import streamlit as st
from groq import Groq

# --- CONFIGURATION ---
# It's best practice to use st.secrets for keys, but for local testing:
GROQ_API_KEY = "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"
client = Groq(api_key=GROQ_API_KEY)

# --- SYSTEM DESIGN ---
# This persona ensures the LLM stays focused on recruitment
SYSTEM_PERSONA = {
    "role": "system",
    "content": (
        "You are 'TalentScout', a professional recruitment assistant. "
        "Phase 1: Politely collect Full Name, Email, Phone, Experience (years), "
        "Position, Location, and Tech Stack. Ask for these one or two at a time. "
        "Phase 2: Once you have all info, generate 3-5 technical questions "
        "specifically tailored to their Tech Stack. "
        "Guidelines: Stay professional, do not deviate from hiring, and "
        "exit gracefully if the user says 'bye' or 'exit'."
    )
}

# --- HELPER FUNCTIONS ---
def get_groq_response(messages):
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"I'm sorry, I encountered an error: {str(e)}"

# --- STREAMLIT UI ---
st.set_page_config(page_title="TalentScout AI", page_icon="🚀")
st.title("🚀 TalentScout Hiring Assistant")
st.caption("Powered by Groq & Llama 3")

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        SYSTEM_PERSONA,
        {"role": "assistant", "content": "Welcome to TalentScout! I'm here to help with your initial screening. To get started, what is your full name and the position you're applying for?"}
    ]

# Display Conversation
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- CHAT INTERACTION ---
if prompt := st.chat_input("Enter your response..."):
    # Append User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Check for Termination
    if any(stop in prompt.lower() for stop in ["exit", "quit", "bye"]):
        farewell = "Thank you for your interest in TalentScout. We will review your details. Have a great day!"
        st.chat_message("assistant").markdown(farewell)
        st.stop()

    # Generate Assistant Response
    with st.chat_message("assistant"):
        response = get_groq_response(st.session_state.messages)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
