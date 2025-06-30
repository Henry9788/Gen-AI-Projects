import streamlit as st
from langchain.agents import initialize_agent, AgentType, Tool
from langchain.chat_models import ChatOpenAI
from langchain_experimental.tools.python.tool import PythonREPLTool
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get Groq API key from environment
groq_api_key = os.getenv("LLAMA3_API_KEY")

#Validate API Key
if not groq_api_key or not groq_api_key.startswith("gsk_"):
    raise ValueError("LLAMA3_API_KEY is missing or invalid. Get one from https://console.groq.com and set it in a .env file.")

# Create a LangChain-compatible Groq chat model (LLaMA 3 70B)
llm = ChatOpenAI(
    model="llama3-70b-8192",
    openai_api_key=groq_api_key,
    openai_api_base="https://api.groq.com/openai/v1",
    temperature=0.2,
)

# Tool to run and evaluate Python code
tools = [PythonREPLTool()]

# Create an agent that can use tools (like Python REPL)
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)

st.title("Code Generator Application using Langchain")
user_prompt = st.text_area("Enter the Python code description:")

if st.button("Generate Code"):
    if user_prompt=="":
        st.warning("Please enter a description.")
    else:
        with st.spinner("Generating code using LLaMA 3..."):
            code = agent.run(user_prompt)
        st.code(code, language="python")