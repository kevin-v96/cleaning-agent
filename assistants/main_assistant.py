from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field

from datetime import datetime
from langchain_core.runnables import Runnable, RunnableConfig

from state import State


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            configuration = config.get("configurable", {})
            thread_id = configuration.get("thread_id", None)
            dialog_state = state.get("dialog_state", "primary_assistant")
            state = {**state, "thread_id": thread_id, "dialog_state": dialog_state}
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
        return {**state, "messages": result}


# Primary Assistant
class ToCleaningBookingAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle bookings of cleaning services."""

    service_required: str = Field(
        description="The type of cleaning service the user needs."
    )
    required_date: str = Field(
        description="The date the user needs the cleaning service."
    )
    service_length_required: int = Field(
        description="The length of the cleaning service the user needs."
    )
    request: str = Field(
        description="Any necessary followup questions the cleaning scheduler assistant should clarify before proceeding."
    )

    class Config:
        schema_extra = {
            "example": {
                "service_required": "House Cleaning",
                "required_date": "2023-07-01",
                "service_length_required": 3,
                "request": "I need house cleaning service.",
            }
        }


class CompleteOrEscalate(BaseModel):
    """A tool to mark the current task as completed and/or to escalate control of the dialog to the main assistant,
    who can re-route the dialog based on the user's needs."""

    cancel: bool = True
    reason: str

    class Config:
        schema_extra = {
            "example": {
                "cancel": True,
                "reason": "The user changed their mind about the current task.",
            },
            "example 2": {
                "cancel": True,
                "reason": "I have fully completed the task.",
            },
            "example 3": {
                "cancel": False,
                "reason": "I need to ask the user for more information.",
            },
        }


primary_assistant_prompt = ChatPromptTemplate.from_messages(
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
primary_assistant_tools = [
    TavilySearchResults(max_results=1),
]
