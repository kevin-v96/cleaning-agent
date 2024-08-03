# env
from dotenv import load_dotenv

import shutil
import uuid

# langgraph
from langchain_core.messages import ToolMessage
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

# utils
from utils import create_tool_node_with_fallback, _print_event, user_id

load_dotenv()

db = "availabilities.sqlite"
backup_file = "availabilities.backup.sqlite"

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

    # Let's create an example conversation a user might have with the assistant
    tutorial_questions = [
        "Hi there, what cleaning services are available?",
        "I need a cleaning service for my home. What are my options?",
        "I need the cleaning service for 3 hours." "The next available option is great",
    ]

    # Update with the backup file so we can restart from the original place in each section
    shutil.copy(backup_file, db)
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
    for question in tutorial_questions:
        events = graph.stream(
            {"messages": ("user", question)}, config, stream_mode="values"
        )
        for event in events:
            _print_event(event, _printed)
        snapshot = graph.get_state(config)
        while snapshot.next:
            # We have an interrupt! The agent is trying to use a tool, and the user can approve or deny it
            # Note: This code is all outside of your graph. Typically, you would stream the output to a UI.
            # Then, you would have the frontend trigger a new run via an API call when the user has provided input.
            user_input = input(
                "Do you approve of the above actions? Type 'y' to continue;"
                " otherwise, explain your requested changed.\n\n"
            )
            if user_input.strip() == "y":
                # Just continue
                result = graph.invoke(
                    None,
                    config,
                )
            else:
                # Satisfy the tool invocation by
                # providing instructions on the requested changes / change of mind
                result = graph.invoke(
                    {
                        "messages": [
                            ToolMessage(
                                tool_call_id=event["messages"][-1].tool_calls[0]["id"],
                                content=f"API call denied by user. Reasoning: '{user_input}'. Continue assisting, accounting for the user's input.",
                            )
                        ]
                    },
                    config,
                )
            snapshot = graph.get_state(config)
