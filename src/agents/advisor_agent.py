"""
PlantPulse Farm Advisor Agent.
Acts as the central coordinator, aggregating findings from soil, moisture, and environmental agents
to generate a consolidated farm report and prioritized recommendations.
"""

import os
from typing import List
from pydantic import BaseModel, Field
from google.adk import Agent
from src.agents.soil_agent import SoilAnalysis
from src.agents.moisture_agent import MoistureAnalysis
from src.agents.environment_agent import EnvironmentAnalysis

# Load model configuration, falling back to gemini-2.5-flash
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# Define the structured output schema using Pydantic.
# The Google ADK and Gemini use this schema to enforce structured JSON output.
class FarmRecommendation(BaseModel):
    overall_plant_health_score: int = Field(
        ...,
        description="Overall plant health score from 0 to 100 aggregated from all sub-analyses.",
        ge=0,
        le=100
    )
    overall_risk_level: str = Field(
        ...,
        description="Overall risk level assessing soil, moisture, and environmental conditions. Must be one of: 'Low', 'Medium', or 'High'."
    )
    priority_actions: List[str] = Field(
        ...,
        description="Actionable remediation steps ranked by priority (High priority actions first)."
    )
    issues_detected: List[str] = Field(
        ...,
        description="Consolidated list of issues detected by all sub-agents."
    )
    final_recommendation: str = Field(
        ...,
        description="A concise, farmer-friendly summary report and directive for the next steps."
    )


# Initialize the Farm Advisor Agent with the structured output schema
advisor_agent = Agent(
    name="advisor_agent",
    model=MODEL_NAME,
    instruction=(
        "You are the PlantPulse Farm Advisor Agent. Your task is to aggregate, correlate, and prioritize "
        "the findings from the Soil Nutrition Agent, Soil Moisture Agent, and Environmental Agent to "
        "create a single, cohesive farm report.\n\n"
        
        "Inputs You Will Receive:\n"
        "- SoilAnalysis: Analysis of Soil Nitrogen, Phosphorus, and Potassium.\n"
        "- MoistureAnalysis: Classification of soil moisture status and watering advice.\n"
        "- EnvironmentAnalysis: Analysis of temperature stress and disease risk.\n\n"
        
        "Your Responsibilities & Priority Rules:\n"
        "1. Aggregate all detected issues from the sub-analyses.\n"
        "2. Rank actions by priority using these rules:\n"
        "   - HIGH Priority: Severe nutrient deficiency, Very dry soil, Overwatered soil, Heat stress, High disease risk.\n"
        "   - MEDIUM Priority: Moderate nutrient deficiencies, Wet soil, Humidity concerns.\n"
        "   - LOW Priority: Minor observations and preventative maintenance.\n"
        "3. Compute an overall plant health score from 0 to 100 based on the sub-scores.\n"
        "4. Determine the overall risk level ('Low', 'Medium', or 'High').\n"
        "5. Write a concise, actionable, and friendly final recommendation for the farmer.\n\n"
        
        "You must output a response adhering strictly to the FarmRecommendation schema."
    ),
    output_schema=FarmRecommendation,
)
