from typing import Annotated

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from typing_extensions import TypedDict
from datetime import datetime
from langchain_core.messages import AIMessage
from pydantic import BaseModel, Field

from langgraph.graph.message import AnyMessage, add_messages
from tools import check_availability, book_service, cancel_booking


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


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
            "If the user asks for anything other than cleaning services, redirect them to a human agent."
            "Under cleaning services, you are only allowed to book slots for general cleaning. If the user asks for anything else, redirect them to a human agent."
            "If the user asks for general cleaning, make sure you ask them what duration they want the service for and tell them the price for the same."
            "The user is not aware of the different specialized assistants, so do not mention them; just quietly delegate through function calls. "
            "Provide detailed information to the customer, and always double-check the database before concluding that information is unavailable. "
            " When searching, be persistent. Expand your query bounds if the first search returns no results. "
            " If a search comes up empty, expand your search before giving up."
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
