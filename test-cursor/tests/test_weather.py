"""Tests for weather module."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

from weather import (
    ForecastAPIError,
    InvalidCoordinatesError,
    get_forecast,
    save_forecast,
)

PARIS_LAT = 48.85
PARIS_LON = 2.35
TZ = "Europe/Paris"


def _api_response() -> dict:
    times = [f"2026-06-04T{i:02d}:00" for i in range(48)]
    return {
        "current_weather": {
            "temperature": 18.5,
            "windspeed": 12.0,
            "weathercode": 2,
            "time": "2026-06-04T14:00",
        },
        "hourly": {
            "time": times,
            "temperature_2m": [float(t) for t in range(48)],
            "precipitation": [0.0] * 48,
        },
    }


def _mock_response(status_code: int, json_data: dict | None = None, text: str = "") -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.text = text or json.dumps(json_data or {})
    response.json.return_value = json_data or {}
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(
            f"{status_code} Error", response=response
        )
    else:
        response.raise_for_status.return_value = None
    return response


@patch("weather.requests.get")
def test_get_forecast_success(mock_get: MagicMock) -> None:
    mock_get.return_value = _mock_response(200, _api_response())

    result = get_forecast(PARIS_LAT, PARIS_LON, TZ)

    assert result["current_weather"]["temperature"] == 18.5
    assert len(result["hourly"]["time"]) == 24
    assert len(result["hourly"]["temperature_2m"]) == 24
    assert len(result["hourly"]["precipitation"]) == 24
    assert result["hourly"]["temperature_2m"][0] == 0.0
    assert result["hourly"]["time"][23] == "2026-06-04T23:00"

    mock_get.assert_called_once()
    call_kwargs = mock_get.call_args
    assert call_kwargs.kwargs["timeout"] == 10
    params = call_kwargs.kwargs["params"]
    assert params["latitude"] == PARIS_LAT
    assert params["longitude"] == PARIS_LON
    assert params["timezone"] == TZ
    assert params["current_weather"] == "true"
    assert params["hourly"] == "temperature_2m,precipitation"


@patch("weather.requests.get")
def test_get_forecast_422(mock_get: MagicMock) -> None:
    mock_get.return_value = _mock_response(
        422,
        text='{"reason":"Invalid timezone"}',
    )

    with pytest.raises(ForecastAPIError, match="422"):
        get_forecast(PARIS_LAT, PARIS_LON, "Invalid/Zone")


@patch("weather.requests.get")
def test_get_forecast_5xx(mock_get: MagicMock) -> None:
    mock_get.return_value = _mock_response(503, text="Service Unavailable")

    with pytest.raises(ForecastAPIError, match="503"):
        get_forecast(PARIS_LAT, PARIS_LON, TZ)


@patch("weather.requests.get")
def test_get_forecast_timeout(mock_get: MagicMock) -> None:
    mock_get.side_effect = requests.Timeout("read timed out")

    with pytest.raises(ForecastAPIError, match="timed out"):
        get_forecast(PARIS_LAT, PARIS_LON, TZ)


@pytest.mark.parametrize(
    "lat, lon",
    [
        (-91.0, 0.0),
        (90.1, 0.0),
        (0.0, -181.0),
        (0.0, 180.1),
    ],
)
def test_get_forecast_invalid_coordinates(lat: float, lon: float) -> None:
    with pytest.raises(InvalidCoordinatesError):
        get_forecast(lat, lon, TZ)


@patch("weather.requests.get")
def test_get_forecast_does_not_call_api_on_invalid_coords(mock_get: MagicMock) -> None:
    with pytest.raises(InvalidCoordinatesError):
        get_forecast(100.0, PARIS_LON, TZ)

    mock_get.assert_not_called()


def test_save_forecast_writes_indented_json_with_timestamp(tmp_path: Path) -> None:
    data = {
        "current_weather": {"temperature": 20.0},
        "hourly": {"time": ["2026-06-04T00:00"], "temperature_2m": [20.0], "precipitation": [0.0]},
    }
    output = tmp_path / "nested" / "forecast.json"

    returned = save_forecast(data, output)

    assert returned == output
    assert output.exists()

    saved = json.loads(output.read_text(encoding="utf-8"))
    assert saved["current_weather"]["temperature"] == 20.0
    assert saved["hourly"]["time"] == ["2026-06-04T00:00"]
    assert "saved_at" in saved
    assert saved["saved_at"].endswith("+00:00") or saved["saved_at"].endswith("Z")

    raw = output.read_text(encoding="utf-8")
    assert "\n" in raw
    assert '  "current_weather"' in raw


@patch("weather.requests.get")
def test_get_forecast_logs_success(mock_get: MagicMock, caplog: pytest.LogCaptureFixture) -> None:
    import logging

    caplog.set_level(logging.INFO)
    mock_get.return_value = _mock_response(200, _api_response())

    get_forecast(PARIS_LAT, PARIS_LON, TZ)

    messages = [record.message for record in caplog.records]
    assert any("Requesting forecast" in msg for msg in messages)
    assert any("Forecast received" in msg for msg in messages)
