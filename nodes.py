from state import State
from typing import Literal, Callable
from langgraph.prebuilt import tools_condition

from langgraph.graph import END
from langchain_core.messages import ToolMessage
from assistants.main_assistant import CompleteOrEscalate, ToCleaningBookingAssistant
from assistants.cleaning_scheduler import cleaning_scheduler_safe_tools


def route_cleaning_scheduler(
    state: State,
) -> Literal[
    "cleaning_scheduler_sensitive_tools",
    "cleaning_scheduler_safe_tools",
    "leave_skill",
    "__end__",
]:
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    safe_toolnames = [t.name for t in cleaning_scheduler_safe_tools]
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "cleaning_scheduler_safe_tools"
    return "cleaning_scheduler_sensitive_tools"


def route_primary_assistant(
    state: State,
) -> Literal[
    "primary_assistant_tools",
    "enter_cleaning_scheduler",
    "__end__",
]:
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        if tool_calls[0]["name"] == ToCleaningBookingAssistant.__name__:
            return "enter_cleaning_scheduler"
        return "primary_assistant_tools"
    raise ValueError("Invalid Route")


# Each delegated workflow can directly respond to the user
# When the user responds, we want to return to the currently active workflow
def route_to_workflow(
    state: State,
) -> Literal[
    "primary_assistant",
    "book_cleaning",
]:
    """If we are in a delegated state, route directly to the appropriate assistant."""
    dialog_state = state.get("dialog_state")
    if not dialog_state:
        return "primary_assistant"
    return dialog_state[-1]


def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    def entry_node(state: State) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user."
                    f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name},"
                    " and the booking, update, or other action is not complete until after you have successfully invoked the appropriate tool."
                    " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the primary host assistant take control."
                    " Do not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id,
                )
            ],
            "dialog_state": new_dialog_state,
        }

    return entry_node
