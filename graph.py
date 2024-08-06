# langchain
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition

from typing import Literal

# utils
from assistants import (
    sensitive_tool_names,
    sensitive_tools,
    safe_tools,
    assistant_prompt,
    ToAskHumanAgent,
    Assistant,
    State,
    redirect_to_human,
    user_id,
)
from utils import create_tool_node_with_fallback


# Define logic
def route_tools(
    state: State,
) -> Literal["ask_human_agent", "safe_tools", "sensitive_tools", "__end__"]:
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
    elif first_tool_call["name"] == ToAskHumanAgent.__name__:
        return "ask_human_agent"
    return "safe_tools"


def build_graph():
    # Define the graph
    llm = ChatOpenAI(model="gpt-4o-mini")
    assistant_runnable = assistant_prompt | llm.bind_tools(safe_tools + sensitive_tools)
    builder = StateGraph(State)

    builder.add_node("fetch_user_id", user_id)
    builder.add_edge(START, "fetch_user_id")

    builder.add_node("assistant", Assistant(assistant_runnable))
    builder.add_edge("fetch_user_id", "assistant")
    builder.add_node("safe_tools", create_tool_node_with_fallback(safe_tools))
    builder.add_node("sensitive_tools", create_tool_node_with_fallback(sensitive_tools))
    builder.add_node("ask_human_agent", redirect_to_human)
    builder.add_edge("ask_human_agent", END)
    builder.add_conditional_edges(
        "assistant",
        route_tools,
        {
            "safe_tools": "safe_tools",
            "sensitive_tools": "sensitive_tools",
            "ask_human_agent": "ask_human_agent",
            END: END,
        },
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

    return graph
