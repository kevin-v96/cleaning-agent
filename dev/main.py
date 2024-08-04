from typing import Annotated

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from typing_extensions import TypedDict

from langgraph.graph.message import AnyMessage, add_messages

from typing import Optional, Union
from langchain_core.tools import tool
import sqlite3
from datetime import datetime, date
from typing import Literal

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition

from tools import create_tool_node_with_fallback, _print_event
from langchain_core.messages import ToolMessage

db = "availabilities.sqlite"
bookings_db = "bookings.sqlite"


def run_chat(graph, user_input, config, _printed) -> None:
    state = graph.get_state(config)
    print(state)
    events = graph.stream(
        {"messages": ("user", str(user_input))}, config, stream_mode="values"
    )
    for event in events:
        _print_event(event, _printed)
    snapshot = graph.get_state(config)
    result = []
    while snapshot.next:
        # We have an interrupt! The agent is trying to use a tool, and the user can approve or deny it
        # Note: This code is all outside of your graph. Typically, you would stream the output to a UI.
        # Then, you would have the frontend trigger a new run via an API call when the user has provided input.
        user_input = input(
            "Do you approve of the above actions? Type 'y' to continue;"
            " otherwise, explain your requested change.\n\n"
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
    return result


@tool
def check_availability(
    service_required: str = "House Cleaning",
    service_length: Optional[int] = None,
) -> list[dict]:
    """
    Search for the next availability for the kind of cleaning service required.

    Args:
        service_required (str): The kind of cleaning service required. Defaults to House Cleaning.
        service_length (Optional[int]): The length of the service offered. Defaults to None.

    Returns:
        list[dict]: A list of next availabilities for the type of cleaning service required by the user.
    """
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    query = "SELECT * FROM availabilities WHERE service = ?"
    params = []
    params.append(f"%{service_required}%")

    if service_length:
        query += " AND service_length LIKE ?"
        params.append(f"%{service_length}%")

    cursor.execute(query, params)
    results = cursor.fetchall()

    conn.close()

    return [
        dict(zip([column[0] for column in cursor.description], row)) for row in results
    ]


@tool
def book_service(
    user_id: int,
    worker_id: int,
    service_required: Optional[str] = "House Cleaning",
    required_date: Optional[Union[datetime, date]] = None,
    service_length_required: Optional[int] = None,
) -> str:
    """
    Book a service for a particular customer.

    Args:
        user_id (int): The ID of the user who is making a booking.
        worker_id (int): The ID of the worker whose service is required.
        service_required (Optional[str]): The kind of service required by the user. Defaults to House Cleaning.
        required_date (Optional[Union[datetime, date]]): The date and time when the service is required. Defaults to None.
        service_length_required (Optional[int]): The length of time for which the service is required.

    Returns:
        str: A message indicating whether the service information was successfully updated or not.
    """
    conn = sqlite3.connect(bookings_db)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO bookings (user_id, worker_id, service_required, required_date, service_length_required) VALUES (?, ?, ?, ?, ?);",
        (user_id, worker_id, service_required, required_date, service_length_required),
    )

    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Added booking for user {user_id} with worker {worker_id} for {required_date} successfully updated."
    else:
        conn.close()
        return f"No record found for worker with ID {worker_id}."


@tool
def cancel_booking(booking_id: int) -> str:
    """
    Cancel a home service booking by its ID.

    Args:
        booking_id (int): The ID of the booking to cancel.

    Returns:
        str: A message indicating whether the booking was successfully cancelled or not.
    """
    conn = sqlite3.connect(db)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM bookings WHERE id = ?", (booking_id,))
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return f"Booking {booking_id} successfully cancelled."
    else:
        conn.close()
        return f"No booking found with ID {booking_id}."


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    thread_id: str


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            result = self.runnable.invoke(state)
            # If the LLM happens to return an empty response, we will re-prompt it
            # for an actual response.
            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}


assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful customer support assistant for Superbench, a home services AI company. "
            "Your primary role is to search for availabilities for different home and cleaning services to answer customer queries. "
            "If a customer requests a cleaning service, "
            "delegate the task to the appropriate specialized assistant by invoking the corresponding tool. You are not able to answer these types of queries yourself."
            " Only the specialized assistants are given permission to do this for the user."
            "The user is not aware of the different specialized assistants, so do not mention them; just quietly delegate through function calls. "
            "Provide detailed information to the customer, and always double-check the database before concluding that information is unavailable. "
            " When searching, be persistent. Expand your query bounds if the first search returns no results. "
            " If a search comes up empty, expand your search before giving up."
            "\n\nCurrent user id:\n<User>\n{thread_id}\n</User>"
            "\nCurrent time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())


# "Read"-only tools (such as retrievers) don't need a user confirmation to use
safe_tools = [check_availability]

# These tools all change the user's reservations.
# The user has the right to control what decisions are made
sensitive_tools = [book_service, cancel_booking]
sensitive_tool_names = {t.name for t in sensitive_tools}

if __name__ == "__main__":
    llm = ChatOpenAI(model="gpt-4o-mini")
    # Our LLM doesn't have to know which nodes it has to route to. In its 'mind', it's just invoking functions.
    assistant_runnable = assistant_prompt | llm.bind_tools(safe_tools + sensitive_tools)
    builder = StateGraph(State)

    builder.add_node("assistant", Assistant(assistant_runnable))
    builder.add_node("safe_tools", create_tool_node_with_fallback(safe_tools))
    builder.add_node("sensitive_tools", create_tool_node_with_fallback(sensitive_tools))
    # Define logic
    builder.add_edge(START, "assistant")

    def route_tools(
        state: State,
    ) -> Literal["safe_tools", "sensitive_tools", "__end__"]:
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
        interrupt_before=["sensitive_tools"],
    )

    _printed = set()

    # Print the greeting message once
    print(
        "Hi, I'm a cleaning service booking assistant for Superbench. How can I help you today?"
    )
    config = {
        "configurable": {
            # Checkpoints are accessed by thread_id
            "thread_id": str(1),
        }
    }

    while True:
        user_input = input()

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        # Call run_chat with the current user input and configuration
        result = run_chat(graph, user_input, config, _printed)
