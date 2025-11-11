# langgraph_workflow.py

from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal
from langchain_core.runnables import Runnable
from langchain_core.messages import AIMessage
#from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import os
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import InMemorySaver

load_dotenv()  # Load environment variables from .env file

# Define the state
class ReviewState(TypedDict):
    input: str
    response: str
    review: Literal["approve", "reject","regenerate",""]
    comment: str
    iteration: int

llm = ChatGroq(model="openai/gpt-oss-120b")

def llm_response(state: ReviewState) -> ReviewState:
    prompt = state["input"]
    comment=""
    if state["comment"]:
        prompt += f"\n\nHuman feedback: {state['comment']}\nPlease revise accordingly."
        comment=state["comment"]
    response = llm.invoke(prompt)
    print (f"Iteration: {state['iteration']}. LLM Response: {response.content}")
    return {
        "input": state["input"],
        "response": response.content,
        "iteration": state["iteration"] + 1,
        "review": "regenerate" if state["comment"] else "",
        "comment": comment
    }

# Human review node
def human_review(state: ReviewState) -> Command[Literal["approval_node","llm_response", "rejection_node"]]:
    print("Awaiting human review...")
    decision = interrupt({
        "question": "Do you approve the following output?",
        "response": state["response"]
    }) # Graph is paused as this line
    print(f"Human decision: {decision}") # Graph resumes here once app.invoke() is called from UI with Command having resume="approve" or "reject"
    if decision == "approve":
        return Command(goto="approval_node", update={"review": "approve"})
    elif decision == "reject" and state["iteration"] < 3:
        return Command(goto="llm_response", update={"review": "regenerate"})
    elif decision == "reject" and state["iteration"] >= 3:
        return Command(goto="rejection_node", update={"review": "reject"})

def final_rejection(state: ReviewState) -> ReviewState:
    state["response"] = "Final rejection after 3 attempts."
    return state

def approve(state: ReviewState) -> ReviewState:
    print(f"Final approved response: {state['response']}")
    return state

# Build the graph
graph = StateGraph(ReviewState)
graph.add_node("llm_response", llm_response)
graph.add_node("human_review", human_review)
graph.add_node("rejection_node", final_rejection)
graph.add_node("approval_node", approve)

graph.set_entry_point("llm_response")
graph.add_edge("llm_response", "human_review")
graph.add_edge("human_review", END)
graph.add_edge("approval_node", END)
graph.add_edge("rejection_node", END)


checkpointer = InMemorySaver()
agent = graph.compile(checkpointer=checkpointer)