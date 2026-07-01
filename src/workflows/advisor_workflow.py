"""
Advisor Workflow module for PlantPulse Guardian AI.
Orchestrates the multi-agent execution graph to produce a consolidated agricultural report.
"""

import os
from google.adk import Agent, Workflow
from src.agents.soil_agent import soil_agent
from src.agents.environment_agent import environment_agent
from src.agents.moisture_agent import moisture_agent
from src.agents.advisor_agent import advisor_agent

# Construct the multi-agent workflow graph.
# The ADK Workflow defines the execution graph from START to the sub-agents, then to the advisor agent.
advisor_workflow = Workflow(
    name="plantpulse_guardian_workflow",
    edges=[
        ("START", soil_agent),
        ("START", environment_agent),
        ("START", moisture_agent),
        (soil_agent, advisor_agent),
        (environment_agent, advisor_agent),
        (moisture_agent, advisor_agent),
    ]
)
