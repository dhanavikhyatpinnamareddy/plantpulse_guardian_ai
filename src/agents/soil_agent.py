"""
Soil Nutrition Advisor Agent.
Analyzes Nitrogen (N), Phosphorus (P), and Potassium (K) levels to evaluate soil health and suggest fertilizers.
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
class SoilAnalysis(BaseModel):
    soil_score: int = Field(
        ...,
        description="A soil fertility score from 0 to 100 assessing overall nutrient balance.",
        ge=0,
        le=100
    )
    issues: List[str] = Field(
        ...,
        description="List of detected nutrient deficiencies, excesses, or imbalances (e.g., 'Low Potassium', 'High Nitrogen')."
    )
    recommendations: List[str] = Field(
        ...,
        description="Actionable recommendations to remedy issues (e.g., 'Apply organic compost', 'Add potassium-rich potash')."
    )


# Initialize the Soil Nutrition Agent with the structured output schema
soil_agent = Agent(
    name="soil_nutrition_agent",
    model=MODEL_NAME,
    instruction=(
        "You are an expert agricultural soil scientist. Your task is to analyze soil macronutrient "
        "readings: Nitrogen (N), Phosphorus (P), and Potassium (K) for a specific field and evaluate crop health.\n\n"
        
        "How to get inputs:\n"
        "1. If a 'sensor_id' is provided, use the 'get_soil_and_weather_metrics' tool to retrieve "
        "the current Nitrogen, Phosphorus, and Potassium readings.\n"
        "2. If raw Nitrogen, Phosphorus, and Potassium values are provided directly in the input, "
        "use those values directly.\n\n"
        
        "Your Responsibilities:\n"
        "- Assess Nitrogen (N), Phosphorus (P), and Potassium (K) levels (optimal levels are generally: "
        "N: 40-60 mg/kg, P: 20-30 mg/kg, K: 30-50 mg/kg).\n"
        "- Detect nutrient deficiencies (values below optimal ranges) and nutrient excesses (values above optimal ranges).\n"
        "- Calculate an overall soil fertility score from 0 to 100 based on how close the N, P, and K values are to their optimal ranges.\n"
        "- Generate a list of actionable issues and recommendations (targeted synthetic or organic fertilizers).\n\n"
        
        "You must output a response adhering strictly to the SoilAnalysis schema."
    ),
    output_schema=SoilAnalysis,
    tools=[get_soil_and_weather_metrics],
)

