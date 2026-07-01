"""
Soil Moisture & Irrigation Advisor Agent.
Analyzes soil moisture levels to determine water adequacy and provide irrigation recommendations.
"""

import os
from typing import List
from pydantic import BaseModel, Field
from google.adk import Agent
from src.tools.sensor_tool import get_soil_and_weather_metrics

# Load model configuration, falling back to gemini-2.5-flash
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# Define the structured output schema using Pydantic.
# The Google ADK and Gemini use this schema to enforce structured JSON output.
class MoistureAnalysis(BaseModel):
    moisture_score: int = Field(
        ...,
        description="A soil moisture health score from 0 to 100 assessing water balance.",
        ge=0,
        le=100
    )
    moisture_status: str = Field(
        ...,
        description="Classification of moisture status. Must be one of: 'Very Dry', 'Dry', 'Optimal', 'Wet', or 'Overwatered'."
    )
    issues: List[str] = Field(
        ...,
        description="List of detected watering/irrigation issues (e.g., 'Soil is critically dry', 'Waterlogging risk')."
    )
    recommendations: List[str] = Field(
        ...,
        description="Actionable precision irrigation recommendations (e.g., 'Initiate drip irrigation', 'Disable sprinklers')."
    )


# Initialize the Soil Moisture Agent with the structured output schema
moisture_agent = Agent(
    name="moisture_agent",
    model=MODEL_NAME,
    instruction=(
        "You are an expert agricultural irrigation engineer and hydrologist. Your task is to evaluate soil "
        "moisture readings (volumetric water content percentage) and formulate precise watering recommendations.\n\n"
        
        "How to get inputs:\n"
        "1. If a 'sensor_id' is provided, use the 'get_soil_and_weather_metrics' tool to retrieve "
        "the current soil moisture reading.\n"
        "2. If raw soil moisture percentage is provided directly in the input, "
        "use that value directly.\n\n"
        
        "Your Responsibilities & Reasoning Guidelines:\n"
        "- Classify the soil moisture status based on the following percentage ranges:\n"
        "  - Below 20%: 'Very Dry'\n"
        "  - 20% to 40%: 'Dry'\n"
        "  - 40% to 70%: 'Optimal'\n"
        "  - 70% to 85%: 'Wet'\n"
        "  - Above 85%: 'Overwatered'\n"
        "- Calculate an overall moisture health score from 0 to 100. (An optimal range should score near 100, while extreme dryness or overwatering should yield low scores).\n"
        "- Identify any water-stress issues for the plants (e.g., drought stress, roots waterlogging).\n"
        "- Generate targeted irrigation recommendations (e.g., schedule, drip vs overhead irrigation, drainage tips).\n\n"
        
        "You must output a response adhering strictly to the MoistureAnalysis schema."
    ),
    output_schema=MoistureAnalysis,
    tools=[get_soil_and_weather_metrics],
)

