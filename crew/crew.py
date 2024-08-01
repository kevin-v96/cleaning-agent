from crewai import Crew, Process

from agents import CleaningServiceAgents
from tasks import CleaningCompanyTasks


class CleaningServiceCrew:
    def __init__(self):
        agents = CleaningServiceAgents()
        self.cleaning_guardrail_agent = agents.cleaning_guardrail_agent()
        self.customer_service_agent = agents.customer_service_agent()

    def kickoff(self):
        self.main_task = input(
            "Hi! I'm a service bot for Superbench. I can help you with queries related to cleaning services. What can I help you with today? "
        )
        tasks = CleaningCompanyTasks()
        crew = Crew(
            agents=[self.cleaning_guardrail_agent, self.customer_service_agent],
            tasks=[
                tasks.guardrail_task(self.main_task, self.cleaning_guardrail_agent),
                tasks.cleaning_service_task(
                    self.main_task, self.customer_service_agent
                ),
                tasks.sql_task(self.customer_service_agent),
            ],
            verbose=True,
            process=Process.sequential,
            memory=True,
            output_log_file=True,
        )
        crew.kickoff()
