"""
Weather module for fetching and storing weather data from Open-Meteo API.
"""

import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create console handler with formatting
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def get_forecast(
    lat: float,
    lon: float,
    timezone: str,
    timeout: int = 10
) -> Dict[str, Any]:
    """
    Fetch weather forecast data from Open-Meteo API.

    Args:
        lat: Latitude coordinate (-90 to 90)
        lon: Longitude coordinate
        timezone: Timezone string (e.g., 'Europe/Paris')
        timeout: Request timeout in seconds (default: 10)

    Returns:
        Dictionary containing current_weather and hourly forecast data

    Raises:
        ValueError: If coordinates are invalid
        requests.exceptions.Timeout: If request exceeds timeout
        requests.exceptions.HTTPError: If API returns error status
    """
    logger.info(f"Fetching forecast for lat={lat}, lon={lon}, tz={timezone}")

    # Validate coordinates
    if not -90 <= lat <= 90:
        logger.error(f"Invalid latitude: {lat}. Must be between -90 and 90")
        raise ValueError(f"Latitude must be between -90 and 90, got {lat}")

    if not -180 <= lon <= 180:
        logger.error(f"Invalid longitude: {lon}. Must be between -180 and 180")
        raise ValueError(f"Longitude must be between -180 and 180, got {lon}")

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": "temperature_2m,precipitation",
        "timezone": timezone,
    }

    try:
        logger.debug(f"Making request to {url} with params {params}")
        response = requests.get(url, params=params, timeout=timeout)

        # Handle 422 Unprocessable Entity
        if response.status_code == 422:
            logger.error(f"422 Unprocessable Entity: Invalid parameters")
            response.raise_for_status()

        # Handle 5xx Server Errors
        if 500 <= response.status_code < 600:
            logger.error(f"API Server Error ({response.status_code})")
            response.raise_for_status()

        # Raise for other HTTP errors
        response.raise_for_status()

        data = response.json()
        logger.info(
            f"Successfully fetched forecast: "
            f"current_weather={data.get('current_weather')}, "
            f"hourly_records={len(data.get('hourly', {}).get('time', []))}"
        )

        return data

    except requests.exceptions.Timeout as e:
        logger.error(f"Request timeout after {timeout}s: {e}")
        raise
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error: {e.response.status_code} - {e}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed: {e}")
        raise


def save_forecast(data: Dict[str, Any], output_path: str) -> None:
    """
    Save forecast data to JSON file with timestamp.

    Args:
        data: Forecast data dictionary
        output_path: Path where to save the JSON file

    Raises:
        IOError: If file cannot be written
        TypeError: If data is not JSON serializable
    """
    logger.info(f"Saving forecast to {output_path}")

    try:
        # Add timestamp to data
        data_with_timestamp = {
            "timestamp": datetime.now().isoformat(),
            "forecast": data,
        }

        # Ensure parent directory exists
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Write to file with indentation
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data_with_timestamp, f, indent=2, ensure_ascii=False)

        logger.info(f"Forecast saved successfully to {output_path}")

    except IOError as e:
        logger.error(f"Failed to write to file {output_path}: {e}")
        raise
    except TypeError as e:
        logger.error(f"Data is not JSON serializable: {e}")
        raise
