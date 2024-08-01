from crewai import Task
from textwrap import dedent


class CleaningCompanyTasks:
    def guardrail_task(self, main_task, agent):
        return Task(
            description=f"Determine whether the main task - {main_task} - is related to cleaning services",
            expected_output=dedent(
                f"""If the customer's main task - {main_task} - is related to cleaning services, the query is redirected to the Customer Service Assistant.
							   If their query is not related to cleaning services, the customer is informed that the agent can only help with cleaning services."""
            ),
            agent=agent,
        )

    def cleaning_service_task(self, main_task, agent):
        return Task(
            description=dedent(
                f"""Determine whether the task - {main_task} - is regular cleaning, or post-renovation cleaning
						   (or any other kind of cleaning). If they ask for regular cleaning, run the sql task.
						   If they ask for any other kind of cleaning, inform them that you are connecting them
						   to a human agent."""
            ),
            expected_output=dedent(
                """If the task is regular cleaning, output the cleaning service for which the next availability is required.
							   If it is anything else, tell the customer you are connecting them to a human agent, and end the run"""
            ),
            agent=agent,
        )

    def sql_task(self, agent):
        return Task(
            description="Run SQL queries to find out the next availability for the required cleaning service",
            expected_output="""SQL queries executed successfully. The result of the query \
        is returned. Inform the customer about the next availability of the cleaning service and end the run.
		Please do not keep running the same queries.""",
            agent=agent,
        )
