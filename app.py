import streamlit as st
from simple_agent import run_agent

# Page config
st.set_page_config(page_title="AI Assistant - Web Search & Math", page_icon="🤖", layout="wide")

st.title("🤖 AI Assistant")
st.markdown("This agent can search the web, answer questions, and solve math problems!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Sidebar with example questions
with st.sidebar:
    st.header("📝 Example Questions")
    st.markdown("- What is the capital of France?")
    st.markdown("- Calculate 15% of 200")
    st.markdown("- Solve: 25 * 4 + 10")
    st.markdown("- What is the square root of 144?")
    st.markdown("- Who won the World Cup in 2018?")
    st.markdown("- Explain quantum computing simply")
    
    st.divider()
    st.markdown("### 🛠️ Features")
    st.markdown("- 🔍 Web Search")
    st.markdown("- 💬 Question Answering")
    st.markdown("- 🧮 Math Problem Solving")
    st.markdown("- 📚 Research Assistant")
    
    st.divider()
    st.caption("Powered by Groq LLM & Tavily Search API")

# Chat input
if prompt := st.chat_input("Ask me anything..."):
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Get response from agent
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = run_agent(prompt)
            st.markdown(response)
    
    # Add assistant response to history
    st.session_state.messages.append({"role": "assistant", "content": response})