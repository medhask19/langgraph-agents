# langgraph-agents

AI Agents using langgraph framework

## Setup instructions

1. Install python 3.11 or higher
2. Install uv package manager. Refer this link for uv installation instructions: <https://docs.astral.sh/uv/getting-started/installation/>
3. Rename env.example to .env file and provide GROQ_API_KEY (Refer [https://console.groq.com/keys](https://console.groq.com/keys) to create GROQ API key using free tier)
4. Clone git repository:
    - `git clone https://github.com/medhask19/langgraph-agents.git`
    - `cd langgraph-agents`
5. Run command: `uv sync` (This will create python virtual environment & install all packages from pyproject.toml)

## 1_simple_agent agent

1. A simple langraph agent with a single `llm_response` node is available /1_simple_agent/
2. Command to run this agent: `uv run .\1_simple_agent\graph.py`

## 2_human_in_loop agent

1. An agent using langgraph's human-in-the-loop workflow is available at /human_in_loop/
2. Run this agent by launching streamlit web interface: `uv run streamlit run human_in_loop/streamlit_ui.py`

## Additional notes

This tutorial uses the GROQ Cloud API for LLM inferencing. GROQ is an AI inference platform designed for developers — it's smart, fast, and cost-effective, with a free tier that’s ideal for small-scale POCs and experimentation.

For more details, visit GROQ Cloud [https://groq.com/groqcloud](https://groq.com/groqcloud)
