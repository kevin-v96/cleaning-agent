from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

system_prompt_template = """You are a customer of a home services company. \
You are interacting with a user who is a customer support person. \

{instructions}

When you are finished with the conversation, respond with a single word 'FINISHED'"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt_template),
        MessagesPlaceholder(variable_name="messages"),
    ]
)
instructions = """Your name is {name}. You are trying to book a regular cleaning services for as close to one week from now as possible. \
You want them to give you the exact appointment details. You want the cleaning service for 3 hours."""

simulated_user_prompt = prompt.partial(name="Kevin", instructions=instructions)
