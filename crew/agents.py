from textwrap import dedent
from crewai import Agent
from composio_langchain import App, ComposioToolSet
import os

toolset = ComposioToolSet(api_key=os.environ["COMPOSIO_API_KEY"])
sql_tools = toolset.get_tools([App.SQLTOOL])


class CleaningServiceAgents:
    def __init__(self):
        pass

    def cleaning_guardrail_agent(self):
        return Agent(
            role="Cleaning Guardrail Agent",
            goal=(
                "To redirect customers to the right agent. If the customer asks for a service related to cleaning, \
			redirect them to the Customer Service Assistant. If they ask for anything else, \
		 tell them that you can only help with cleaning services."
            ),
            backstory=dedent(
                """\
				As a Cleaning Guardrail Agent for a Home Services Company, you are adept at listening
					to customer queries, and figuring out if their queries are related to cleaning services."""
            ),
            verbose=True,
            allow_delegation=True,
        )

    def customer_service_agent(self):
        return Agent(
            role="Customer Service Assistant",
            goal="To redirect customers to the right agent. If the customer asks for cleaning related services, running SQL queries to find out the next availability for the required cleaning service",
            backstory=dedent(
                """\
				As a Customer Service Assistant for a Home Services Company, you are adept at listenint
				to customer queries, figuring out what services they need and how to get them the service.
				You listen with empathy, figure out the customer needs, and if they need cleaning services, tell them the next availability.
                You do this by running SQL queries to get the availability of the cleaning staff and the customer's preferred time.
				Connect to the local SQLite DB at connection string = availabilities.db
            	Try to analyze the tables first by listing all the tables and columns
            	and doing distinct values for each column and once sure, make a query to
            	get the data you need."""
            ),
            verbose=True,
            allow_delegation=False,
            tools=sql_tools,
            max_iter=10,
        )
