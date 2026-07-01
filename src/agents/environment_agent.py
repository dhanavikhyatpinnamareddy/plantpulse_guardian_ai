"""
Environmental Advisor Agent.
Analyzes ambient temperature and relative humidity to identify crop environmental stress and disease risks.
"""

import os
from typing import List, Optional
from pydantic import BaseModel, Field
from google.adk import Agent
from src.tools.sensor_tool import get_soil_and_weather_metrics

# Load model configuration, falling back to gemini-2.5-flash
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


# Define the structured output schema using Pydantic.
# The Google ADK and Gemini use this schema to enforce structured JSON output.
class EnvironmentAnalysis(BaseModel):
    environment_score: int = Field(
        ...,
        description="An environmental health score from 0 to 100 assessing ambient conditions.",
        ge=0,
        le=100
    )
    risk_level: str = Field(
        ...,
        description="Overall environmental risk level. Must be one of: 'Low', 'Medium', or 'High'."
    )
    issues: List[str] = Field(
        ...,
        description="List of detected environmental issues (e.g., 'Heat Stress', 'High Disease Risk', 'Dry Air Stress')."
    )
    recommendations: List[str] = Field(
        ...,
        description="Actionable recommendations to mitigate environmental risks or protect crops."
    )


# Initialize the Environmental Agent with the structured output schema
environment_agent = Agent(
    name="environmental_agent",
    model=MODEL_NAME,
    instruction=(
        "You are an expert agricultural micro-climate scientist and plant pathologist. Your task is to "
        "analyze atmospheric sensor data (temperature, relative humidity) and optional weather forecast "
        "data to assess crop stress and disease risks.\n\n"
        
        "How to get inputs:\n"
        "1. If a 'sensor_id' is provided, use the 'get_soil_and_weather_metrics' tool to retrieve "
        "the current temperature and humidity readings.\n"
        "2. If raw temperature and humidity are provided directly in the input, "
        "use those values directly.\n"
        "3. Look for any optional 'weather_forecast' data in the input to anticipate upcoming trends "
        "(e.g., incoming frost, heatwaves, or heavy rain) and incorporate this into your recommendations.\n\n"
        
        "Your Responsibilities & Reasoning Guidelines:\n"
        "- Analyze Temperature:\n"
        "  - Below 15°C: Classify as 'Cold Stress'.\n"
        "  - 15°C to 35°C: Classify as 'Optimal'.\n"
        "  - Above 35°C: Classify as 'Heat Stress'.\n"
        "- Analyze Humidity:\n"
        "  - Below 30%: Classify as 'Dry Air Stress'.\n"
        "  - 30% to 80%: Classify as 'Optimal'.\n"
        "  - Above 80%: Classify as 'High Disease Risk' (due to pathogen or fungal growth factors).\n"
        "- Determine the overall risk_level ('Low', 'Medium', or 'High') and environment_score (0-100).\n"
        "  - Scoring starts at 100. Deduct points for temperature stresses, dry air, high humidity disease risk, "
        "    and adverse forecast alerts.\n"
        "- Generate actionable mitigation recommendations (e.g., ventilation, shading, frost covers, pest/fungal monitoring).\n\n"
        
        "You must output a response adhering strictly to the EnvironmentAnalysis schema."
    ),
    output_schema=EnvironmentAnalysis,
    tools=[get_soil_and_weather_metrics],
)

