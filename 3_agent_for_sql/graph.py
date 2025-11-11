from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
import sqlite3
import pandas as pd
from typing import TypedDict, Optional
from dotenv import load_dotenv
import os
load_dotenv()  # Load environment variables from .env file

# ---------- Define State ----------
class State(TypedDict):
    """Defines the data structure passed between nodes."""
    user_query: str
    sql_query: Optional[str]
    result: Optional[str]
    response: Optional[str]


# Connect to SQLite
conn = sqlite3.connect("sqllite-db/sales.db")

# Initialize Groq LLM
llm = ChatGroq(model="openai/gpt-oss-120b")

# ---------- Define LangGraph nodes ----------

def generate_sql(state: State) -> State:
    """Use Groq LLM to translate English to SQL"""
    user_query = state["user_query"]
    
    prompt = PromptTemplate.from_template("""
    You are an expert data analyst. Translate the following natural language question
    into a valid SQLite SQL query for a table named 'sales' with columns:
    order_id, customer, region, product, quantity, price.
    Only return the SQL query without explanation.

    Question: {user_query}
    """)
    sql_query = llm.invoke(prompt.format(user_query=user_query)).content.strip()
    state["sql_query"] = sql_query
    return state


def execute_sql(state: State) -> State:
    """Run SQL query and return result"""
    sql = state["sql_query"]
    try:
        df = pd.read_sql_query(sql, conn)
        result = df.to_string(index=False)
    except Exception as e:
        result = f"Error executing SQL: {e}"
    state["result"] = result
    return state


def format_response(state: State) -> State:
    """Return final formatted output"""
    response = f"🧠 SQL: {state['sql_query']}\n\n📊 Result:\n{state['result']}"
    state["response"] = response
    return state


# ---------- Build the graph ----------

graph = StateGraph(State)
graph.add_node("generate_sql", generate_sql)
graph.add_node("execute_sql", execute_sql)
graph.add_node("format", format_response)

graph.set_entry_point("generate_sql")
graph.add_edge("generate_sql", "execute_sql")
graph.add_edge("execute_sql", "format")
graph.add_edge("format", END)

chain = graph.compile()

# ---------- Chat loop ----------

while True:
    user_input = input("\n💬 Ask a question about sales data (or type 'exit'): ")
    if user_input.lower() == "exit":
        break

    result = chain.invoke({"user_query": user_input})
    print("\n" + result["response"])
