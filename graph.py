# env
from dotenv import load_dotenv

import uuid

# langgraph
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, StateGraph, START
from langchain_openai import ChatOpenAI

# state
from state import State, pop_dialog_state

# assistants
from assistants.main_assistant import (
    CompleteOrEscalate,
    ToCleaningBookingAssistant,
    primary_assistant_prompt,
    primary_assistant_tools,
    Assistant,
)
from assistants.cleaning_scheduler import (
    cleaning_scheduler_safe_tools,
    cleaning_scheduler_sensitive_tools,
    cleaning_scheduler_tools,
    cleaning_scheduler_prompt,
)

# nodes
from nodes import (
    create_entry_node,
    route_cleaning_scheduler,
    route_primary_assistant,
    route_to_workflow,
)

# chat
from chat import run_chat

# utils
from utils import create_tool_node_with_fallback, user_id

load_dotenv()

db = "availabilities.sqlite"

if __name__ == "__main__":
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=1)

    book_cleaning_runnable = cleaning_scheduler_prompt | llm.bind_tools(
        cleaning_scheduler_tools + [CompleteOrEscalate]
    )

    assistant_runnable = primary_assistant_prompt | llm.bind_tools(
        primary_assistant_tools + [ToCleaningBookingAssistant]
    )

    builder = StateGraph(State)
    builder.add_node("fetch_user_id", user_id)
    builder.add_edge(START, "fetch_user_id")

    # Flight booking assistant
    builder.add_node(
        "enter_cleaning_scheduler",
        create_entry_node("Cleaning Service Booking Assistant", "book_cleaning"),
    )
    builder.add_node("book_cleaning", Assistant(book_cleaning_runnable))
    builder.add_edge("enter_cleaning_scheduler", "book_cleaning")
    builder.add_node(
        "cleaning_scheduler_sensitive_tools",
        create_tool_node_with_fallback(cleaning_scheduler_sensitive_tools),
    )
    builder.add_node(
        "cleaning_scheduler_safe_tools",
        create_tool_node_with_fallback(cleaning_scheduler_safe_tools),
    )
    builder.add_edge("cleaning_scheduler_sensitive_tools", "book_cleaning")
    builder.add_edge("cleaning_scheduler_safe_tools", "book_cleaning")
    builder.add_conditional_edges("book_cleaning", route_cleaning_scheduler)
    builder.add_node("leave_skill", pop_dialog_state)
    builder.add_edge("leave_skill", "primary_assistant")

    # Primary assistant
    builder.add_node("primary_assistant", Assistant(assistant_runnable))
    builder.add_node(
        "primary_assistant_tools",
        create_tool_node_with_fallback(primary_assistant_tools),
    )
    # The assistant can route to one of the delegated assistants,
    # directly use a tool, or directly respond to the user
    builder.add_conditional_edges(
        "primary_assistant",
        route_primary_assistant,
        {
            "enter_cleaning_scheduler": "enter_cleaning_scheduler",
            "primary_assistant_tools": "primary_assistant_tools",
            END: END,
        },
    )
    builder.add_edge("primary_assistant_tools", "primary_assistant")
    builder.add_conditional_edges("fetch_user_id", route_to_workflow)

    # compile graph
    memory = SqliteSaver.from_conn_string(":memory:")
    graph = builder.compile(
        checkpointer=memory,
        interrupt_before=[
            "cleaning_scheduler_sensitive_tools",
        ],
    )

    thread_id = str(uuid.uuid4())

    config = {
        "configurable": {
            # The user_id is used to keep a track of the user we are currently serving. In this case, we are using the thread_id as the user_id
            "user_id": thread_id,
            # Checkpoints are accessed by thread_id
            "thread_id": thread_id,
        }
    }

    _printed = set()

    user_input = input(
        "Hi, I'm a cleaning service booking assistant for Superbench. How can I help you today?\n"
    )
    result = run_chat(graph, user_input, config, _printed)
