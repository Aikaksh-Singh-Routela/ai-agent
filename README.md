\# 🤖 AI Agent with Tools

A powerful AI assistant that can search the web, perform calculations, and generate images — all in one conversation.


\## 🚀 Live Demo


\*\*\[Click here to try the live app](https://ai-agent-hk4rpybstfld23lwokqduz.streamlit.app/)\*\*


🔗 Links

GitHub: github.com/Aikaksh-Singh-Routela/ai-agent

AI Image Generator: ai-art-generator-ochre.vercel.app

## 🛠️ Features

| Tool | What It Does |
|------|--------------|
| 🔍 **Web Search** | Get current information from the internet |
| 🧮 **Calculator** | Solve math problems instantly |
| 🎨 **Image Generation** | Create images using my own GPU worker (AI Horde) |

## 📸 Example Prompts

- `"Calculate 50 * 20"`
- `"What is the capital of France?"`
- `"Generate an image of a cute cat"`
- `"Search for news about AI and generate a futuristic robot image"`

## 🏗️ Tech Stack

- **Frontend:** Streamlit
- **LLM:** Groq (Llama 3.3 70B)
- **Web Search:** Tavily API
- **Image Generation:** AI Horde (my own GPU worker)
- **Language:** Python

## 🔧 Local Setup

```bash
git clone https://github.com/Aikaksh-Singh-Routela/ai-agent.git
cd ai-agent
pip install -r requirements.txt
streamlit run app.py
🔑 Environment Variables
Create a .streamlit/secrets.toml file:

toml
GROQ_API_KEY = "your_groq_api_key"
TAVILY_API_KEY = "your_tavily_api_key"

📂 Project Structure
text
ai-agent/
├── app.py                 # Streamlit frontend
├── simple_agent.py        # Agent logic and tools
├── requirements.txt       # Dependencies
└── .streamlit/
    └── secrets.toml       # API keys (not in repo)
🎯 Why This Project Matters
This isn't just an API wrapper. It's an intelligent agent that:

Decides which tool to use based on your question

Orchestrates multiple APIs (Groq, Tavily, AI Horde)

Runs on my own GPU worker for image generation

📄 License
MIT
