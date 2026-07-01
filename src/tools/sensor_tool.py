"""
Sensor Tool module for PlantPulse Guardian AI.
Provides functions to read crop and soil environmental metrics.
"""

from typing import Dict, Any


def get_soil_and_weather_metrics(sensor_id: str) -> Dict[str, Any]:
    """Retrieves real-time crop and soil metrics from a specific field sensor node.

    Args:
        sensor_id: The unique identifier of the sensor device (e.g., 'sensor-north-01').

    Returns:
        A dictionary containing soil nutrients and atmospheric readings:
        - nitrogen (N): Soil Nitrogen level in mg/kg (optimal ~ 40-60)
        - phosphorus (P): Soil Phosphorus level in mg/kg (optimal ~ 20-30)
        - potassium (K): Soil Potassium level in mg/kg (optimal ~ 30-50)
        - temperature: Ambient temperature in degrees Celsius
        - humidity: Relative humidity percentage
        - soil_moisture: Volumetric water content percentage
    """
    # Skeleton placeholder. In a production environment, this would call a IoT API or database.
    return {
        "sensor_id": sensor_id,
        "nitrogen": 45,        # mg/kg
        "phosphorus": 22,      # mg/kg
        "potassium": 38,       # mg/kg
        "temperature": 28.5,    # °C
        "humidity": 68.0,      # %
        "soil_moisture": 35.0   # %
    }
