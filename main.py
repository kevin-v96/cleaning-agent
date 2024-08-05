from assistants import (
    sensitive_tool_names,
    sensitive_tools,
    safe_tools,
    assistant_prompt,
    Assistant,
    State,
)
from langchain_openai import ChatOpenAI
from utils import create_tool_node_with_fallback
from typing import Literal
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition
import uuid
from langchain_core.messages import HumanMessage
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

llm = ChatOpenAI(model="gpt-4o-mini")

assistant_runnable = assistant_prompt | llm.bind_tools(safe_tools + sensitive_tools)

builder = StateGraph(State)

builder.add_node("assistant", Assistant(assistant_runnable))
builder.add_edge(START, "assistant")
builder.add_node("safe_tools", create_tool_node_with_fallback(safe_tools))
builder.add_node("sensitive_tools", create_tool_node_with_fallback(sensitive_tools))


# Define logic
def route_tools(state: State) -> Literal["safe_tools", "sensitive_tools", "__end__"]:
    next_node = tools_condition(state)
    # If no tools are invoked, return to the user
    if next_node == END:
        return END
    ai_message = state["messages"][-1]
    # This assumes single tool calls. To handle parallel tool calling, you'd want to
    # use an ANY condition
    first_tool_call = ai_message.tool_calls[0]
    if first_tool_call["name"] in sensitive_tool_names:
        return "sensitive_tools"
    return "safe_tools"


builder.add_conditional_edges(
    "assistant",
    route_tools,
)
builder.add_edge("safe_tools", "assistant")
builder.add_edge("sensitive_tools", "assistant")

memory = SqliteSaver.from_conn_string(":memory:")
graph = builder.compile(
    checkpointer=memory,
    # NEW: The graph will always halt before executing the "tools" node.
    # The user can approve or reject (or even alter the request) before
    # the assistant continues
    interrupt_before=["sensitive_tools"],
)

thread_id = str(uuid.uuid4())

config = {
    "configurable": {
        "thread_id": thread_id,
    }
}


def respond_to_user(graph, user_input, thread_id):
    final_state = graph.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config={"configurable": {"thread_id": thread_id}},
    )

    return final_state["messages"][-1].content


app = FastAPI()


class Message(BaseModel):
    user_id: str
    content: str


@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")


@app.post("/chatbot/")
def chatbot(message: Message):
    return {
        "response": respond_to_user(graph, message.content, message.user_id),
        "user_id": message.user_id,
    }
