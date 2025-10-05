from typing import TypedDict
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END
from dotenv import load_dotenv
import os
load_dotenv()  # Load environment variables from .env file

class State(TypedDict):
    input: str
    response: str

def llm_response(state: State) -> State:
    llm = ChatGroq(model="openai/gpt-oss-120b")
    prompt = state["input"]
    response = llm.invoke(prompt)
    return {
        "input": state["input"],
        "response": response.content
    }

graph = StateGraph(State)
graph.add_node("llm_response", llm_response)
graph.set_entry_point("llm_response")
graph.add_edge("llm_response", END)

agent = graph.compile()
while True:
    user_input = input("Enter your input prompt(Type 'exit' or 'q' to quit): ")
    if user_input.lower() in ["exit", "quit", "q"]:
        break
    response = agent.invoke({"input": user_input, "response": ""})
    print(f"LLM Response: {response['response']}")