import streamlit as st
from model import ChatModel
from config import config

# Page config
st.set_page_config(page_title="AI Chatbot", page_icon="🤖")

# Load model only once
@st.cache_resource
def load_model():
    return ChatModel(model_name=config.MODEL_NAME, max_history=config.MAX_HISTORY_LENGTH)

try:
    chat_model = load_model()
except Exception as e:
    st.error(f"Error loading model: {e}")
    st.stop()

# Header
st.title("🤖 AI Chatbot")
st.write("Powered by DialoGPT")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! I'm an AI chatbot. How can I help you today?"}
    ]

# Display chat messages from history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Type your message..."):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                response = chat_model.generate_response(prompt)
                st.markdown(response)
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": response})
            except Exception as e:
                st.error(f"Error generating response: {e}")

# Sidebar controls
with st.sidebar:
    st.header("Settings")
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm an AI chatbot. How can I help you today?"}
        ]
        chat_model.clear_history()
        st.rerun()
