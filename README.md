A bot with multiple agents written in CrewAI. It helps route the user to thei required cleaning service. Alternatively, for services we don't have any information for, it informs them that they are being redirected to a human agent.

I've used Poetry for package management, so once poetry is installed on your system, running `poetry install --no-root` will install all the requirements. Then, running `poetry run python runcrew.py` will run the crew on the command line.

## TO-DO
- [ ] Add FastAPI
- [ ] Add gradio interface
- [ ] Add the crew as nodes in a LangGraph graph
- [ ] Add containerization