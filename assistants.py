# langchain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import AIMessage
from langgraph.graph.message import AnyMessage, add_messages

from typing import Annotated
from typing_extensions import TypedDict
from datetime import datetime
from pydantic import BaseModel, Field

# utils
from tools import check_availability, book_service, cancel_booking, check_bookings


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_id: str


def user_id(state: State, config: RunnableConfig):
    return {**state, "user_id": config["configurable"]["thread_id"]}


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
            else:
                break
        return {"messages": result}


def redirect_to_human(state: State):
    return {
        "messages": [
            AIMessage(
                content="Sorry, I can't help with that. Redirecting you to a human agent."
            )
        ]
    }


class ToAskHumanAgent(BaseModel):
    """Transfers work to a human agent in case the service the user requires is anything other than the bot is programmed to answer."""

    service_required: str = Field(description="The service required by the user.")
    request: str = Field(
        description="Any additional information or requests from the user regarding the service required."
    )

    class Config:
        json_schema_extra = {
            "example": {
                "service_required": "Plumbing",
                "request": "I need plumbing service next week.",
            }
        }


assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful customer support assistant for Superbench, a home services AI company. "
            "Your primary role is to search for availabilities for different home and cleaning services to answer customer queries. "
            "If a customer requests a cleaning service, "
            "delegate the task to the appropriate specialized assistant by invoking the corresponding tool. You are not able to answer these types of queries yourself."
            " Only the specialized assistants are given permission to do this for the user."
            " You can help with three things - booking general cleaning, checking availability of services in the future, and cancelling bookings."
            " You have to use tools for all three of these things."
            "If the user asks for anything other than booking, checking availability of, and cancelling cleaning services, redirect them to a human agent."
            "Under cleaning services, you are only allowed to book slots for general cleaning. If the user asks for anything else, redirect them to a human agent."
            "If the user at any point asks you to connect them with a human agent (or you decide to do so), just mock the behaviour to do so. Don't tell them that you're unable to connect them."
            "If the user asks for general cleaning, make sure you ask them what duration they want the service for and tell them the price for the same."
            "The user is not aware of the different specialized assistants, so do not mention them; just quietly delegate through function calls. "
            "Provide detailed information to the customer, and always double-check the database before concluding that information is unavailable. "
            " When searching, be persistent. Expand your query bounds if the first search returns no results. "
            " If a search comes up empty, expand your search before giving up."
            "\nUse this as the user id of the current user: {user_id}."
            "\nCurrent time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

safe_tools = [check_availability, check_bookings]
sensitive_tools = [book_service, cancel_booking]
sensitive_tool_names = {t.name for t in sensitive_tools}
