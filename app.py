# langchain
from langchain_core.messages import HumanMessage

# api
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

# utils
from graph import build_graph
from dotenv import load_dotenv

load_dotenv()


class Message(BaseModel):
    user_id: str
    content: str


def respond_to_user(graph, message):
    config = {"configurable": {"thread_id": message.user_id}}
    if message.content.lower() == "y":
        final_state = graph.invoke(None, config)
    else:
        final_state = graph.invoke(
            {"messages": [HumanMessage(content=message.content)]},
            config,
        )

    snapshot = graph.get_state(config)
    if snapshot.next and snapshot.next[0] == "sensitive_tools":
        return "Please confirm the action by responding with 'y'."

    return final_state["messages"][-1].content


app = FastAPI()
graph = build_graph()


@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")


@app.post("/chatbot/")
def chatbot(message: Message):
    return {
        "response": respond_to_user(graph, message),
    }
