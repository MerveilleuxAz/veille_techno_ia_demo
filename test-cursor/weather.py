"""Open-Meteo forecast client."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone as dt_timezone
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

BASE_URL = "https://api.open-meteo.com/v1/forecast"
REQUEST_TIMEOUT = 10
HOURLY_HOURS = 24


class InvalidCoordinatesError(ValueError):
    """Raised when latitude or longitude is out of range."""


class ForecastAPIError(Exception):
    """Raised when the forecast API returns an error or the request fails."""


def _validate_coordinates(lat: float, lon: float) -> None:
    if not -90 <= lat <= 90:
        raise InvalidCoordinatesError(
            f"Latitude must be between -90 and 90, got {lat}"
        )
    if not -180 <= lon <= 180:
        raise InvalidCoordinatesError(
            f"Longitude must be between -180 and 180, got {lon}"
        )


def _slice_hourly(hourly: dict[str, Any]) -> dict[str, list[Any]]:
    return {
        "time": hourly.get("time", [])[:HOURLY_HOURS],
        "temperature_2m": hourly.get("temperature_2m", [])[:HOURLY_HOURS],
        "precipitation": hourly.get("precipitation", [])[:HOURLY_HOURS],
    }


def get_forecast(lat: float, lon: float, timezone: str) -> dict[str, Any]:
    """
    Fetch current weather and the next 24 hourly values from Open-Meteo.

    Raises:
        InvalidCoordinatesError: Invalid lat/lon before any HTTP call.
        ForecastAPIError: Timeout, HTTP 422, HTTP 5xx, or other request failure.
    """
    _validate_coordinates(lat, lon)

    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "hourly": "temperature_2m,precipitation",
        "timezone": timezone,
    }

    logger.info(
        "Requesting forecast lat=%.4f lon=%.4f timezone=%s",
        lat,
        lon,
        timezone,
    )

    try:
        response = requests.get(
            BASE_URL,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.Timeout as exc:
        logger.error("Forecast request timed out after %ss", REQUEST_TIMEOUT)
        raise ForecastAPIError(
            f"Forecast request timed out after {REQUEST_TIMEOUT}s"
        ) from exc
    except requests.RequestException as exc:
        logger.error("Forecast request failed: %s", exc)
        raise ForecastAPIError(f"Forecast request failed: {exc}") from exc

    if response.status_code == 422:
        logger.error("API returned 422: %s", response.text)
        raise ForecastAPIError(
            f"Invalid forecast parameters (422): {response.text}"
        )

    if response.status_code >= 500:
        logger.error(
            "API returned %s: %s", response.status_code, response.text
        )
        raise ForecastAPIError(
            f"Forecast service error ({response.status_code}): {response.text}"
        )

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        logger.error("Unexpected HTTP error: %s", exc)
        raise ForecastAPIError(f"Forecast request failed: {exc}") from exc

    payload = response.json()
    result = {
        "current_weather": payload.get("current_weather"),
        "hourly": _slice_hourly(payload.get("hourly", {})),
    }

    logger.info(
        "Forecast received (%d hourly steps)",
        len(result["hourly"]["time"]),
    )
    return result


def save_forecast(data: dict[str, Any], output_path: str | Path) -> Path:
    """Write forecast data to JSON with indentation and a UTC timestamp."""
    path = Path(output_path)
    envelope = {
        **data,
        "saved_at": datetime.now(dt_timezone.utc).isoformat(),
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(envelope, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    logger.info("Forecast saved to %s", path)
    return path
