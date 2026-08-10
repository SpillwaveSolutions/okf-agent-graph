from crewai import Agent, Crew, Process, Task

researcher = Agent(
    role="Senior Researcher",
    goal="Find accurate primary sources",
    backstory="You are a meticulous analyst who cites sources.",
    max_iter=6,
    allow_delegation=False,
)

manager = Agent(
    role="Research Manager",
    goal="Coordinate researchers and synthesize findings",
    backstory="You orchestrate specialists and enforce quality bars.",
)

crew = Crew(
    agents=[researcher],
    tasks=[Task(description="Investigate topic", agent=researcher)],
    process=Process.hierarchical,
    manager_agent=manager,
)
