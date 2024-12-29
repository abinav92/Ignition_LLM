import pandas as pd
from datetime import datetime
import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

st.title("🏭 SCADA*i*")

USER_AVATAR = "🧑🏻"
BOT_AVATAR = "🤖"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get the username from query parameters
username = st.query_params.get("username", [None])
sessionid = st.query_params.get("sessionid", [None])

# Initialize or load chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = str(sessionid)

# Function to append messages to CSV
def append_to_csv(message_store):
    try:
        df = pd.DataFrame([message_store])
        df.to_csv('conversation_history.csv', mode='a', index=False, header=not pd.io.common.file_exists('conversation_history.csv'))
    except Exception as e:
        st.error(f"Error saving message to CSV: {e}")

# Function to trim messages to fit within token limits
def trim_messages(messages, max_tokens=50000):
    trimmed_messages = []
    token_count = 0

    for message in reversed(messages):
        # Approximate token count per message
        message_tokens = len(message["content"].split()) + 5  # Adding 5 as buffer for role and metadata
        if token_count + message_tokens > max_tokens:
            break
        trimmed_messages.insert(0, message)
        token_count += message_tokens

    return trimmed_messages

# Display chat messages
for message in st.session_state.messages:
    avatar = USER_AVATAR if message["role"] == "user" else BOT_AVATAR
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# Welcome the user and greet them
if len(st.session_state.messages) == 0:
    greeting = f"Hello, {username}! How can I assist you today?"
    st.session_state.messages.append({"role": "assistant", "content": greeting})
    append_to_csv({
        "Date & Time": datetime.now(), 
        "Session ID": str(st.session_state.session_id), 
        "Role": "assistant", 
        "Content": greeting,
        "Username": str(username)
    })
    
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        st.markdown(greeting)

# Main chat interface
if prompt := st.chat_input("How can I help?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    append_to_csv({
        "Date & Time": datetime.now(), 
        "Session ID": str(st.session_state.session_id), 
        "Role": "user", 
        "Content": prompt, 
        "Username": str(username)
    })
    
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        message_placeholder = st.empty()
        full_response = ""
        try:
            trimmed_messages = trim_messages(st.session_state["messages"])
            for response in client.chat.completions.create(
                model="gpt-4o",
                messages=trimmed_messages,
                stream=True
            ):
                full_response += response.choices[0].delta.content or ""
                message_placeholder.markdown(full_response + "|")
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            append_to_csv({
                "Date & Time": datetime.now(), 
                "Session ID": str(st.session_state.session_id), 
                "Role": "assistant", 
                "Content": full_response,
                "Username": str(username)
            })
        except Exception as e:
            st.error(f"Error generating response: {e}")

if st.button("Clear Chat Conversation"):
    st.session_state.messages = []
    st.success("Chat conversation cleared.")