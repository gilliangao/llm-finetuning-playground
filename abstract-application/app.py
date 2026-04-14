import streamlit as st
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader, select_autoescape, TemplateNotFound
from typing import Any
import os
import dotenv

dotenv.load_dotenv()

st.set_page_config(page_title="Abstractinator") # Set the title of the browser tab
def chat_response(system_prompt : str, user_prompt : str, model : str, temperature : float) -> str:
    client = OpenAI()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature,
        max_tokens=400
    )

    content = response.choices[0].message.content
    tokens = response.usage

    return content, tokens


def generate_abstract(topic, model, temperature):
    generation_system_prompt = load_template("./prompts/system.jinja", {})
    generation_user_prompt = load_template(
        "./prompts/user.jinja",
        {
            "topic": topic,
        }
    )

    fake_abstract, tokens = chat_response(generation_system_prompt, generation_user_prompt, model, temperature)

    return fake_abstract, tokens


def load_template(template_filepath: str, arguments: dict[str, Any]) -> str:
    try:
        # Get the directory of the current script
        current_dir = os.path.dirname(os.path.abspath(__file__)) # (1)!
        # Set up the Jinja environment with the correct base path
        env = Environment(
            loader=FileSystemLoader(searchpath=current_dir),
            autoescape=select_autoescape()
        )
        template = env.get_template(template_filepath)
        return template.render(**arguments)

    except TemplateNotFound:
        st.error(f"Template file not found: {template_filepath}")
        return None
    

#streamlit component code -widges
# Streamlit app
st.title("Fake Abstract Generator")

# User input
# Streamlit app
st.title("Fake Abstract Generator")

# User input
topic = st.text_input("Enter a topic sentence:")
# Generate button
if st.button("Generate Abstract"):
    if topic:
        with st.spinner("Generating abstract..."):
            abstract = generate_abstract(topic)
        st.subheader("Generated Abstract:")
        st.write(abstract)
    else:
        st.warning("Please enter a topic sentence.")

# Add some information about the app
st.sidebar.header("About")
st.sidebar.info(
    "This app generates fake abstracts based on a given topic sentence using AI. "
    "Enter a topic and click 'Generate Abstract' to see the result."
)

#Temperature and model
# Sidebar controls
st.sidebar.header("Settings")
temperature = st.sidebar.slider("Temperature", min_value=0.0, max_value=2.0, value=0.2, step=0.01)
model = st.sidebar.selectbox("Model", ["gpt-4o-mini", "gpt-4o"])

#Tracking tokens and spending
#We need to keep track of tokens and costs across multiple generations. This means we need to use the session_state functionality.

import yaml
import json

# Initialize session state
if 'total_tokens' not in st.session_state:
    st.session_state.total_tokens = 0
if 'total_cost' not in st.session_state:
    st.session_state.total_cost = 0
if 'sent_tokens' not in st.session_state:
    st.session_state.sent_tokens = 0
if 'sent_cost' not in st.session_state:
    st.session_state.sent_cost = 0
if 'received_tokens' not in st.session_state:
    st.session_state.received_tokens = 0
if 'received_cost' not in st.session_state: 
    st.session_state.received_cost = 0

# add config yaml to session_state
if 'config' not in st.session_state:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, "config.yml"), "r") as config_file:
        config = yaml.safe_load(config_file)
    st.session_state.config = config

def update_usage_statistics(tokens, model):
    st.sidebar.header("Usage Statistics")
    st.sidebar.metric("Total Tokens Sent", f"{st.session_state.sent_tokens:,}")
    st.sidebar.metric("Total Tokens Received", f"{st.session_state.received_tokens:,}")
    st.sidebar.metric("Total Tokens Used", f"{st.session_state.total_tokens:,}")
    st.sidebar.metric("Total Cost ($)", f"{st. session_state.total_cost:.6f}")

    with open("session_state.json", "w") as f:
        json.dump(st.session_state, f)

def update_costs(tokens, model):
    sent_tokens = tokens.prompt_tokens
    received_tokens = tokens.completion_tokens
    total_tokens = sent_tokens + received_tokens
    
    sent_cost = sent_tokens * st.session_state.config["costs"][model]['input'] / 1000
    received_cost = received_tokens * st.session_state.config["costs"][model]['output'] / 1000
    total_cost = sent_cost + received_cost / 1000

    st.session_state.total_tokens += total_tokens
    st.session_state.total_cost += total_cost
    st.session_state.sent_tokens += sent_tokens
    st.session_state.sent_cost += sent_cost
    st.session_state.received_tokens += received_tokens
    st.session_state.received_cost += received_cost

update_costs(tokens, model)
update_usage_statistics()