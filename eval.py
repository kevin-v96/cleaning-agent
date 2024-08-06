from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.messages import AIMessage
from app import respond_to_user
from graph import build_graph
from langgraph.graph import END, MessageGraph, START
from langchain_community.adapters.openai import convert_message_to_dict
from eval_data import simulated_user_prompt


def chat_bot_node(messages):
    graph = build_graph()
    messages = [convert_message_to_dict(m) for m in messages]
    # Call the chat bot
    message_content = "" if not messages else messages[-1]["content"]
    user_id = "1234"
    graph_message = {"user_id": user_id, "content": message_content}
    chat_bot_response = respond_to_user(
        graph, graph_message
    )  # need to change the format here so that the function can be called
    # Respond with an AI Message
    return AIMessage(content=chat_bot_response)


def _swap_roles(messages):
    new_messages = []
    for m in messages:
        if isinstance(m, AIMessage):
            new_messages.append(HumanMessage(content=m.content))
        else:
            new_messages.append(AIMessage(content=m.content))
    return new_messages


def simulated_user_node(messages):
    model = ChatOpenAI(model="gpt-4o-mini")
    simulated_user = simulated_user_prompt | model
    # Swap roles of messages
    new_messages = _swap_roles(messages)
    # Call the simulated user
    response = simulated_user.invoke({"messages": new_messages})
    # This response is an AI message - we need to flip this to be a human message
    return HumanMessage(content=response.content)


def should_continue(messages):
    if len(messages) > 6:
        return "end"
    elif messages[-1].content == "FINISHED":
        return "end"
    else:
        return "continue"


def build_simulation_graph():
    graph_builder = MessageGraph()
    graph_builder.add_node("user", simulated_user_node)
    graph_builder.add_node("chat_bot", chat_bot_node)
    # Every response from  your chat bot will automatically go to the
    # simulated user
    graph_builder.add_edge("chat_bot", "user")
    graph_builder.add_conditional_edges(
        "user",
        should_continue,
        # If the finish criteria are met, we will stop the simulation,
        # otherwise, the virtual user's message will be sent to your chat bot
        {
            "end": END,
            "continue": "chat_bot",
        },
    )
    # The input will first go to your chat bot
    graph_builder.add_edge(START, "chat_bot")
    simulation = graph_builder.compile()
    return simulation


if __name__ == "__main__":
    simulation = build_simulation_graph()
    for chunk in simulation.stream([]):
        # Print out all events aside from the final end chunk
        if END not in chunk:
            print(chunk)
            print("----")
