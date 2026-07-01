"""
Main entry point for PlantPulse Guardian AI.
Loads environment configuration and demonstrates how to execute the multi-agent workflow.
"""

import asyncio
import os
from dotenv import load_dotenv
from src.workflows.advisor_workflow import advisor_workflow

# Load local environment configurations from .env
load_dotenv()

# Verify that the Gemini API Key is configured
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    print("[WARNING]: GEMINI_API_KEY is not set or is using the default placeholder in .env.")
    print("Please obtain an API key from Google AI Studio and configure it.")


async def run_advisor(sensor_id: str):
    """Programmatic execution of the advisor workflow."""
    print(f"[*] Initializing PlantPulse Guardian AI diagnostic for: {sensor_id}...")
    
    # In a fully implemented ADK project, workflows are executed asynchronously.
    # The ADK runtime automatically resolves dependency order, executes tools,
    # passes contexts between agents, and returns the aggregated output.
    #
    # Example execution (placeholder for now):
    # result = await advisor_workflow.run(
    #     input={"sensor_id": sensor_id}
    # )
    # print("[+] Diagnostic Report:\n", result)
    
    print("[✓] Skeleton execution completed. Set your GEMINI_API_KEY to run the full agents.")


if __name__ == "__main__":
    # Standard Python async entry point
    asyncio.run(run_advisor(sensor_id="sensor-north-01"))
