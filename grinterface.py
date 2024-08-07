import gradio as gr
from graph import build_graph
import time

graph = build_graph()


def predict(message, history):
    gpt_response = graph.invoke(
        {"messages": [message]}, {"configurable": {"thread_id": "1234"}}
    )
    print(gpt_response)
    last_message_content = gpt_response["messages"][-1].content
    for i in range(len(last_message_content)):
        time.sleep(0.01)
        yield last_message_content[: i + 1]


gr.ChatInterface(
    predict,
    chatbot=gr.Chatbot(height=300),
    textbox=gr.Textbox(
        placeholder="Ask me about cleaning services", container=False, scale=7
    ),
    title="Superbench AI",
    description="Ask me about booking home services.",
    theme="soft",
    examples=[
        "Hello",
        "What services do you have available?",
        "Could I book a plumbing service?",
    ],
    cache_examples=True,
    retry_btn=None,
    undo_btn="Delete Previous",
    clear_btn="Clear",
).launch()
