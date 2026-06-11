import os
from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain.tools import tool
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate

from tools.web_search import web_search
from tools.image_gen import generate_image
from tools.calculator import calculator

@tool
def search(query: str) -> str:
    """Search the web for current information."""
    return web_search(query)

@tool
def generate(prompt: str) -> str:
    """Generate an image from a text description."""
    result = generate_image(prompt)
    if result.startswith("http"):
        return f"Here is your generated image: {result}"
    return result

@tool
def calculate(expression: str) -> str:
    """Perform mathematical calculations."""
    return calculator(expression)

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    temperature=0.7,
    api_key="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"
)

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful AI assistant with access to tools: search, generate, and calculate.

Use search for current information (news, facts, data).
Use generate to create images from text descriptions.
Use calculate for math problems.

You can use multiple tools in sequence.
"""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

agent = create_tool_calling_agent(
    llm=llm,
    tools=[search, generate, calculate],
    prompt=prompt
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=[search, generate, calculate],
    verbose=True,
    handle_parsing_errors=True
)

def run_agent(user_input: str) -> str:
    result = agent_executor.invoke({"input": user_input})
    return result["output"]