import sqlite3
import pandas as pd
from typing import TypedDict, Optional
from langchain.tools import tool
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
load_dotenv()  # Load environment variables from .env file



# -------------------------------
# STEP 1: SQLite Setup
# -------------------------------
conn = sqlite3.connect("sqllite-db/sales.db")

# -------------------------------
# STEP 2: Define Tools
# -------------------------------
@tool("run_sql_query")
def run_sql_query(sql: str) -> str:
    """Executes a SQL query on the 'sales' SQLite table and returns the result."""
    print(f"🛠️ [Tool] Executing SQL:\n{sql}\n")
    try:
        df = pd.read_sql_query(sql, conn)
        if df.empty:
            return "No matching records found."
        return df.to_string(index=False)
    except Exception as e:
        return f"Error executing SQL: {e}"


@tool("get_table_schema")
def get_table_schema() -> str:
    """Returns schema of the 'sales' table for SQL generation help."""
    return """
    Table: sales
    Columns:
      - order_id (INTEGER)
      - customer (TEXT)
      - region (TEXT)
      - product (TEXT)
      - quantity (INTEGER)
      - price (REAL)
      - total (REAL)
    """

# -------------------------------
# STEP 3: Define LangGraph State
# -------------------------------
class State(TypedDict):
    user_query: str
    sql_query: Optional[str]
    query_result: Optional[str]
    response: Optional[str]


# -------------------------------
# STEP 4: Initialize LLM + Tools
# -------------------------------
# Tip: Prefer a model you have access to — e.g. "llama-3.1-8b-instant"
llm = ChatGroq(model="openai/gpt-oss-120b")

llm_with_tools = llm.bind_tools([get_table_schema, run_sql_query])


# -------------------------------
# STEP 5: Define Nodes
# -------------------------------
def llm_node(state: State):
    """LLM generates SQL or decides which tool to call."""
    print("🧠 [LLM] Understanding question...")
    table_schema = get_table_schema.invoke({})
    msg = llm_with_tools.invoke(
        f"User asked: {state['user_query']}\n"
        f"Use 'run_sql_query' tool to answer this using the 'sales' table."
        f"Here is the exact schema of 'sales' table that you must use to generate SQL query for the user query. Schema: {table_schema}. Do not invent schema on your own."
    )

    print(f"🧠 [LLM] Generated response/tool calls: {msg}")
    state["response"] = msg
    return state


def tool_node(state: State):
    """Execute tool calls made by LLM."""
    msg = state["response"]

    print("🛠️ [Tool Node] Processing tool calls...\n")
    print(f"🧠 [LLM Message]: {msg}\n")

    # If no tool call, just return the content
    if not hasattr(msg, "tool_calls") or not msg.tool_calls:
        state["response"] = msg.content
        return state

    for tool_call in msg.tool_calls:
        tool_name = tool_call["name"]
        args = tool_call.get("args", {})

        print(f"🛠️ [Tool] Invoking tool: {tool_name} with args: {args}")

        if tool_name == "run_sql_query":
            sql = args.get("sql")
            if not sql:
                # LLM didn’t provide SQL, ask again using schema
                schema = get_table_schema.invoke({})
                followup = llm_with_tools.invoke(
                    f"Generate a SQL query for this question:\n{state['user_query']}\n"
                    f"Schema:\n{schema}\nReturn SQL string only."
                )
                sql = followup.content.strip()
            print(f"🧾 [SQL Generated]\n{sql}\n")
            state["sql_query"] = sql
            result = run_sql_query.invoke({"sql": sql})
            state["query_result"] = result
            print("🛠️ [Tool] SQL executed successfully.")
            print(f"🧾 [SQL Result]\n{result}\n")
        elif tool_name == "get_table_schema":
            schema = get_table_schema.invoke({})
            state["query_result"] = schema
        else:
            state["query_result"] = f"Unknown tool: {tool_name}"

    return state


def summarize_node(state: State):
    state["response"] = state.get('query_result', '')
    
    return state


# -------------------------------
# STEP 6: Build Graph
# -------------------------------
graph = StateGraph(State)
graph.add_node("llm", llm_node)
graph.add_node("tool", tool_node)
graph.add_node("summarize", summarize_node)

graph.set_entry_point("llm")
graph.add_edge("llm", "tool")
graph.add_edge("tool", "summarize")
graph.add_edge("summarize", END)

chain = graph.compile()

# -------------------------------
# STEP 7: Run Chat Loop
# -------------------------------
print("🤖 LangGraph SQL Agent (Groq + SQLite)")
print("Type 'exit' to quit.\n")

while True:
    user_input = input("💬 Ask: ")
    if user_input.lower() == "exit":
        break

    result = chain.invoke({"user_query": user_input})
    print("\n📊 Answer:\n", result["response"])
