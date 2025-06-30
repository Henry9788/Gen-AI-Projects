import streamlit as st
from crewai import Agent, Task, Crew
from dotenv import load_dotenv
from langchain.chat_models import ChatLiteLLM
import os

load_dotenv()
groq_api_key = os.getenv("LLAMA3_API_KEY")

llm = ChatLiteLLM(
    model="llama3-70b-8192",
    api_key=groq_api_key,
    api_base="https://api.groq.com/openai/v1",
    api_type="openai",
    api_provider="groq",
    temperature=0.7
)

ui_designer = Agent(
    role="UI Designer",
    goal="Create HTML structure for the requested web page",
    backstory="Expert in semantic HTML and user-friendly layouts.",
    verbose=True,
    llm=llm
)

styling_agent = Agent(
    role="CSS Stylist",
    goal="Apply Bootstrap or Tailwind CSS based on instructions",
    backstory="Proficient in modern frontend styling using utility-first and component-based CSS.",
    verbose=True,
    llm=llm
)

php_agent = Agent(
    role="PHP Developer",
    goal="Write PHP code to handle backend logic",
    backstory="Expert in writing clean PHP code and handling form submissions, database operations.",
    verbose=True,
    llm=llm
)

st.set_page_config(page_title="Multi-Agent Web Code Generator", layout="wide")
st.title("Multi-Agent Web Code Generator")

user_prompt = st.text_area(
    "Describe the web page you want",
    height=100,
    placeholder="Example: Build a login page using Bootstrap and PHP backend"
)

if st.button("Generate Code") and user_prompt.strip():
    task_html = Task(
        description=f"Based on this prompt: {user_prompt}, create an HTML structure for the web page.",
        expected_output="A clean HTML5 layout with appropriate form or content elements.",
        agent=ui_designer
    )

    task_css = Task(
        description="Style the HTML using Tailwind CSS or Bootstrap as requested.",
        expected_output="HTML with proper CSS classes applied.",
        agent=styling_agent,
        context=[task_html]
    )

    task_php = Task(
        description="Write PHP code to handle backend logic such as form submission.",
        expected_output="PHP code that handles form POST data and returns success or error message.",
        agent=php_agent,
        context=[task_html]
    )

    with st.spinner("Agents are collaborating..."):
        try:
            crew = Crew(
                agents=[ui_designer, styling_agent, php_agent],
                tasks=[task_html, task_css, task_php],
                verbose=True
            )
            crew.kickoff()

            html_code = task_html.output or "No HTML generated."
            css_code = task_css.output or "No CSS generated."
            php_code = task_php.output or "No PHP generated."

            st.subheader("Generated Code Output")
            st.markdown("### HTML")
            st.code(html_code, language="html")

            st.markdown("### CSS / Styled HTML")
            st.code(css_code, language="html")

            st.markdown("### PHP")
            st.code(php_code, language="php")

        except Exception as e:
            st.error(f" Error during code generation: {e}")
else:
    st.info("Enter a prompt and click 'Generate Code' to start.")