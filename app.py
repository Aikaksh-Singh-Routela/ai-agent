import streamlit as st
import time
from simple_agent import run_agent

st.set_page_config(page_title="AI Agent with Tools", page_icon="🤖")

st.title("🤖 AI Agent with Tools")
st.markdown("This agent can calculate math, search the web, and generate images!")

with st.sidebar:
    st.markdown("### 🛠️ Available Tools")
    st.markdown("🧮 **Calculator** - Math problems")
    st.markdown("🔍 **Web Search** - Current information")
    st.markdown("🎨 **Image Generation** - Create images")
    st.markdown("### 📝 Example prompts")
    st.markdown('"Calculate 50 * 20"')
    st.markdown('"What is the capital of France?"')
    st.markdown('"Generate an image of a cute cat"')

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "image_url" in message:
            st.image(message["image_url"])

if prompt := st.chat_input("Ask me something..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            response = run_agent(prompt)
            
            # Check if response is an image URL
            if response.startswith("http") and (".png" in response or ".jpg" in response or ".webp" in response):
                st.image(response)
                st.session_state.messages.append({"role": "assistant", "content": "Here's your image", "image_url": response})
            else:
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})