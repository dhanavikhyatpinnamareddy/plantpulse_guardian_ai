"""
Test script for the PlantPulse Guardian AI multi-agent workflow.
Executes Soil, Moisture, Environmental, and Advisor Agents with sample stress data
and prints their structured outputs with detailed logging.
"""

import asyncio
import os
import json
from dotenv import load_dotenv

# Load local environment configurations (contains GEMINI_API_KEY)
load_dotenv()

from google.adk.runners import InMemoryRunner

# Import our agents
from src.agents.soil_agent import soil_agent
from src.agents.moisture_agent import moisture_agent
from src.agents.environment_agent import environment_agent
from src.agents.advisor_agent import advisor_agent


async def run_testing():
    # 1. Setup sample input values reflecting stress conditions
    sample_data = {
        "nitrogen": 25,          # Low (optimal ~ 40-60)
        "phosphorus": 30,        # Optimal (optimal ~ 20-30)
        "potassium": 15,         # Low (optimal ~ 30-50)
        "temperature": 36.0,     # Heat Stress (above 35°C)
        "humidity": 85.0,        # High Disease Risk (above 80%)
        "soil_moisture": 30.0,   # Dry (dry range 20-40%)
        "weather_forecast": "Hot and sunny today, risk of isolated thunderstorms tomorrow."
    }

    print("=" * 60)
    print("      PLANT PULSE GUARDIAN AI - WORKFLOW DIAGNOSTIC TEST      ")
    print("=" * 60)
    print(f"[*] Starting diagnostic run using model configuration...")
    print(f"[*] Input Metrics:")
    print(json.dumps(sample_data, indent=2))
    print("-" * 60)

    # Verify that GEMINI_API_KEY is available
    if not os.getenv("GEMINI_API_KEY"):
        print("[ERROR]: GEMINI_API_KEY environment variable is missing!")
        print("Please copy .env.example to .env and set your Gemini API key.")
        return

    try:
        # ----------------------------------------------------
        # Step 2. Execute Soil Agent
        # ----------------------------------------------------
        print("\n[Step 1/4] Running Soil Nutrition Advisor Agent...")
        soil_runner = InMemoryRunner(agent=soil_agent)
        soil_input = {
            "nitrogen": sample_data["nitrogen"],
            "phosphorus": sample_data["phosphorus"],
            "potassium": sample_data["potassium"]
        }
        # Run agent and fetch output response
        soil_response = await soil_runner.run_debug(str(soil_input))
        print("[SUCCESS] Soil Agent Completed.")
        print(f"Soil Analysis Response:\n{soil_response}")

        # ----------------------------------------------------
        # Step 3. Execute Moisture Agent
        # ----------------------------------------------------
        print("\n[Step 2/4] Running Soil Moisture & Irrigation Agent...")
        moisture_runner = InMemoryRunner(agent=moisture_agent)
        moisture_input = {
            "soil_moisture": sample_data["soil_moisture"]
        }
        moisture_response = await moisture_runner.run_debug(str(moisture_input))
        print("[SUCCESS] Moisture Agent Completed.")
        print(f"Moisture Analysis Response:\n{moisture_response}")

        # ----------------------------------------------------
        # Step 4. Execute Environment Agent
        # ----------------------------------------------------
        print("\n[Step 3/4] Running Environmental Advisor Agent...")
        env_runner = InMemoryRunner(agent=environment_agent)
        env_input = {
            "temperature": sample_data["temperature"],
            "humidity": sample_data["humidity"],
            "weather_forecast": sample_data["weather_forecast"]
        }
        env_response = await env_runner.run_debug(str(env_input))
        print("[SUCCESS] Environmental Agent Completed.")
        print(f"Environmental Analysis Response:\n{env_response}")

        # ----------------------------------------------------
        # Step 5. Execute Coordinator / Advisor Agent
        # ----------------------------------------------------
        print("\n[Step 4/4] Running PlantPulse Farm Advisor Agent (Consolidator)...")
        advisor_runner = InMemoryRunner(agent=advisor_agent)
        
        # We aggregate all sub-agent outputs as inputs to the main advisor
        advisor_input = {
            "SoilAnalysis": soil_response,
            "MoistureAnalysis": moisture_response,
            "EnvironmentAnalysis": env_response
        }
        
        advisor_response = await advisor_runner.run_debug(str(advisor_input))
        print("[SUCCESS] Farm Advisor Agent Completed.")

        # ----------------------------------------------------
        # Step 6. Output Consolidated Summary
        # ----------------------------------------------------
        print("\n" + "=" * 60)
        print("                 DIAGNOSTIC REPORT SUMMARY                   ")
        print("=" * 60)
        print(f"Final Farm Recommendation:\n{advisor_response}")
        print("=" * 60)

    except Exception as e:
        print(f"\n[ERROR] An exception occurred during execution: {e}")
        print("Verify your python environment has all dependencies installed.")


if __name__ == "__main__":
    asyncio.run(run_testing())
