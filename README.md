A bot that helps route the user to their required cleaning service. Alternatively, for services we don't have any information for, it informs them that they are being redirected to a human agent.

I've used Poetry for package management, so once poetry is installed on your system, running `poetry install --no-root` will install all the requirements.

## How to use
Firstly, you'll have to generate the database of availabilities and bookings. To do this, run `poetry run python database.py`. this will generate `availabilities.sqlite` and `bookings.sqlite`.

Running `poetry run uvicorn app:app --reload` will start a uvicorn server. You can send a POST request to `http://127.0.0.1:8000/chatbot`, with a schema as such: `{"content": str, "user_id": str}` and the bot will send back a response with the schema: `{"response": str}`.

Aside: `poetry run pre-commit install` will make sure the pre-commit hooks run to accomplish all the tasks like linting, typechecking, etc. You can also run those checks manually with `poetry run pre-commit run --all-files`. You can add more pre-commit checks by adding hooks to the `.pre-commit-config.yaml` file.

I checked out a few of the currently popular multi-ai-agent frameworks (CrewAI, LangGraph, AutoGen) to see what fit this particular task. You can find some of those experimentations here:
- [GitHub: multi-agent-ai](https://github.com/kevin-v96/multi-agent-ai)
- [GitHub: multi-agent-ai-tutorials](https://github.com/kevin-v96/multi-agent-ai-tutorials)

I found that out of the three that I tested, CrewAI has the simplest interface and lends itself to simple tasks such as this. Moreover, AutoGen and LangGraph add some (in my opinion) unneccesary complexity to their interface which makes it hard to scale them down for simple tasks (but they, especially LangGraph, are better for more complex tasks especially when it comes to human input interrupts).

## Example Runs
I'm adding some runs during development here:
![Simple output asking for house cleaning on a particular date](images/simple_output.png)

## TO-DO
- [x] add thread id support for multi-user memory
- [x] Add FastAPI
- [x] Add example runs
- [ ] Add Evaluations
- [ ] Red-teaming the bot
### Longer-term TO-DOs
- [ ] Add gradio interface
- [ ] Add the crew as nodes in a LangGraph graph
- [ ] Add containerization

## References
- [Creating a Multi-Agent Chatbot Using AutoGen: An End-to-End Guide](https://blog.arjun-g.com/creating-a-multi-agent-chatbot-using-autogen-an-end-to-end-guide-78b6671a96b4)
- [DeepLearning.ai - Multi AI Agent Systems with CrewAI](https://learn.deeplearning.ai/courses/multi-ai-agent-systems-with-crewai)
- [DeepLearning.ai - AI Agentic Design Patterns with AutoGen](https://learn.deeplearning.ai/courses/ai-agentic-design-patterns-with-autogen)
- [How to Build a SQL Agent with CrewAI and Composio](https://www.analyticsvidhya.com/blog/2024/07/sql-agent-with-crewai-and-composio/)
 - [CrewAI Docs](https://docs.crewai.com/)
 - [FastAPI Docs](https://fastapi.tiangolo.com/)
 - [LangGraph Docs](https://langchain-ai.github.io/langgraph/tutorials/customer-support/customer-support/)
 - [Pre-commit Docs](https://pre-commit.com/)
 - [LangServe Docs](https://python.langchain.com/v0.2/docs/langserve/)
 - [Example of using CrewAI and LangGraph together](https://github.com/crewAIInc/crewAI-examples/tree/main/CrewAI-LangGraph)
