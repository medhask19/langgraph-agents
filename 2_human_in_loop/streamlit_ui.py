# streamlit_ui.py

import streamlit as st
from graph import agent
import time
import uuid
from langgraph.types import Command

thread_id = "user-123"  # In a real app, this would be dynamic per user/session
config = {"configurable": {"thread_id": thread_id}}

st.title("Human-in-the-Loop Review System")

if "state" not in st.session_state:
    st.session_state.state = {
        "input": "",
        "response": "",
        "review": "",
        "comment": "",
        "iteration": 0
    }

# Initial input
if st.session_state.state["iteration"] == 0:
    user_input = st.text_area("Enter your prompt:")
    if st.button("Generate Response"):
        st.session_state.state["input"] = user_input
        st.session_state.state["comment"] = ""
        st.session_state.state = agent.invoke(st.session_state.state, config=config)
        print(f"Generated Response: {st.session_state.state['response']}")

if "submitted" not in st.session_state:
    st.session_state.submitted = False

def submit_review():
    # Reset values safely
    st.session_state.review_option = "approve"
    st.session_state.comment_area = ""
    st.session_state.submitted = True


if st.session_state.state["iteration"] > 0:
    st.subheader(f"LLM Response (Attempt {st.session_state.state['iteration']})")
    st.write(st.session_state.state["response"])

    # Review options
    review = st.radio("Do you approve this response?", ["approve", "reject"], key="review_option")
    comment = ""

    if review == "reject":
        comment = st.text_area("Provide feedback for revision:", key="comment_area")
       

    if st.button("Submit Review"):
        st.session_state.submitted = False
        st.session_state.state["review"] = review
        st.session_state.state["comment"] = comment if not st.session_state.state["comment"] else st.session_state.state["comment"] + "\n" + comment
        if review == "approve":
            st.session_state.state=agent.invoke(Command(resume="approve"), config=config)
        else:
            st.session_state.state=agent.invoke(Command(resume="reject",update={"comment":st.session_state.state["comment"]}), config=config)
        
        print(f"Iteration {st.session_state.state['iteration']}  response: {st.session_state.state['response']}. \nReview status: {st.session_state.state['review']}")

    if st.session_state.state["review"] == "approve":
        st.success(f"✅ Response approved!: {st.session_state.state['response']}")
    elif st.session_state.state["iteration"] >= 3 and st.session_state.state["review"] == "reject":
        st.error("❌ Final rejection after 3 attempts.")
    elif st.session_state.state["review"] == "regenerate":
        print(f"Review Status: {st.session_state.state['review']}")
        
        if not st.session_state.submitted:
            st.button("Generate revised response", on_click=submit_review)
        else:
            st.success("Check revised response", icon="👆")
            

st.write("")
st.write("")
st.write("")

# Reset
if st.button("Start Over"):
    st.session_state.state = {
        "input": "",
        "response": "",
        "review": "",
        "comment": "",
        "iteration": 0
    }
    st.session_state.submitted = False