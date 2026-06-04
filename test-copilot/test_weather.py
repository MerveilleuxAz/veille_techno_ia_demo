"""
Comprehensive tests for weather module.
"""

import json
import pytest
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock
import requests

from weather import get_forecast, save_forecast


class TestGetForecast:
    """Tests for get_forecast function."""

    def setup_method(self):
        """Setup mock response data for tests."""
        self.valid_response_data = {
            "latitude": 48.85,
            "longitude": 2.35,
            "timezone": "Europe/Paris",
            "current_weather": {
                "temperature": 15.5,
                "windspeed": 10.0,
                "time": "2026-06-04T12:00"
            },
            "hourly": {
                "time": [f"2026-06-04T{i:02d}:00" for i in range(24)],
                "temperature_2m": [15 + i*0.5 for i in range(24)],
                "precipitation": [0.0] * 24
            }
        }

    @patch('weather.requests.get')
    def test_get_forecast_success(self, mock_get):
        """Test successful forecast retrieval."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.valid_response_data
        mock_get.return_value = mock_response

        result = get_forecast(48.85, 2.35, "Europe/Paris")

        assert result == self.valid_response_data
        assert result["current_weather"]["temperature"] == 15.5
        assert len(result["hourly"]["time"]) == 24

        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert call_args[1]["timeout"] == 10
        assert call_args[1]["params"]["latitude"] == 48.85

    @patch('weather.requests.get')
    def test_get_forecast_422_unprocessable_entity(self, mock_get):
        """Test handling of 422 Unprocessable Entity error."""
        mock_response = MagicMock()
        mock_response.status_code = 422
        
        error = requests.exceptions.HTTPError("422 Client Error")
        error.response = mock_response
        mock_response.raise_for_status.side_effect = error
        mock_get.return_value = mock_response

        with pytest.raises(requests.exceptions.HTTPError):
            get_forecast(48.85, 2.35, "Europe/Paris")

        mock_get.assert_called_once()

    @patch('weather.requests.get')
    def test_get_forecast_500_server_error(self, mock_get):
        """Test handling of 500 Server Error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        
        error = requests.exceptions.HTTPError("500 Server Error")
        error.response = mock_response
        mock_response.raise_for_status.side_effect = error
        mock_get.return_value = mock_response

        with pytest.raises(requests.exceptions.HTTPError):
            get_forecast(48.85, 2.35, "Europe/Paris")

        mock_get.assert_called_once()

    @patch('weather.requests.get')
    def test_get_forecast_503_service_unavailable(self, mock_get):
        """Test handling of 503 Service Unavailable error."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        
        error = requests.exceptions.HTTPError("503 Service Unavailable")
        error.response = mock_response
        mock_response.raise_for_status.side_effect = error
        mock_get.return_value = mock_response

        with pytest.raises(requests.exceptions.HTTPError):
            get_forecast(48.85, 2.35, "Europe/Paris")

    @patch('weather.requests.get')
    def test_get_forecast_timeout(self, mock_get):
        """Test handling of timeout exception."""
        mock_get.side_effect = requests.exceptions.Timeout("Request timeout")

        with pytest.raises(requests.exceptions.Timeout):
            get_forecast(48.85, 2.35, "Europe/Paris", timeout=10)

        mock_get.assert_called_once()

    @patch('weather.requests.get')
    def test_get_forecast_custom_timeout(self, mock_get):
        """Test custom timeout parameter."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = self.valid_response_data
        mock_get.return_value = mock_response

        get_forecast(48.85, 2.35, "Europe/Paris", timeout=5)

        call_args = mock_get.call_args
        assert call_args[1]["timeout"] == 5

    def test_get_forecast_invalid_latitude_too_high(self):
        """Test rejection of latitude > 90."""
        with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
            get_forecast(91, 2.35, "Europe/Paris")

    def test_get_forecast_invalid_latitude_too_low(self):
        """Test rejection of latitude < -90."""
        with pytest.raises(ValueError, match="Latitude must be between -90 and 90"):
            get_forecast(-91, 2.35, "Europe/Paris")

    def test_get_forecast_invalid_longitude_too_high(self):
        """Test rejection of longitude > 180."""
        with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
            get_forecast(48.85, 181, "Europe/Paris")

    def test_get_forecast_invalid_longitude_too_low(self):
        """Test rejection of longitude < -180."""
        with pytest.raises(ValueError, match="Longitude must be between -180 and 180"):
            get_forecast(48.85, -181, "Europe/Paris")

    def test_get_forecast_boundary_latitude_90(self):
        """Test valid boundary latitude (90)."""
        with patch('weather.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.valid_response_data
            mock_get.return_value = mock_response

            # Should not raise
            get_forecast(90, 0, "UTC")

    def test_get_forecast_boundary_latitude_minus_90(self):
        """Test valid boundary latitude (-90)."""
        with patch('weather.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = self.valid_response_data
            mock_get.return_value = mock_response

            # Should not raise
            get_forecast(-90, 0, "UTC")

    @patch('weather.requests.get')
    def test_get_forecast_connection_error(self, mock_get):
        """Test handling of connection errors."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        with pytest.raises(requests.exceptions.ConnectionError):
            get_forecast(48.85, 2.35, "Europe/Paris")


class TestSaveForecast:
    """Tests for save_forecast function."""

    def setup_method(self):
        """Setup test data."""
        self.test_data = {
            "latitude": 48.85,
            "longitude": 2.35,
            "current_weather": {
                "temperature": 15.5,
                "windspeed": 10.0
            },
            "hourly": {
                "time": ["2026-06-04T00:00", "2026-06-04T01:00"],
                "temperature_2m": [14.0, 13.5],
                "precipitation": [0.0, 0.0]
            }
        }

    def test_save_forecast_creates_file(self):
        """Test that forecast is saved to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "forecast.json"

            save_forecast(self.test_data, str(output_path))

            assert output_path.exists()
            assert output_path.stat().st_size > 0

    def test_save_forecast_json_format(self):
        """Test that saved file is valid JSON with indentation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "forecast.json"

            save_forecast(self.test_data, str(output_path))

            with open(output_path, "r") as f:
                saved_data = json.load(f)

            assert "timestamp" in saved_data
            assert "forecast" in saved_data
            assert saved_data["forecast"] == self.test_data

    def test_save_forecast_timestamp_format(self):
        """Test that timestamp is in ISO format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "forecast.json"

            save_forecast(self.test_data, str(output_path))

            with open(output_path, "r") as f:
                saved_data = json.load(f)

            # Should be parseable as ISO format
            timestamp = datetime.fromisoformat(saved_data["timestamp"])
            assert isinstance(timestamp, datetime)

    def test_save_forecast_creates_parent_directories(self):
        """Test that parent directories are created automatically."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "nested" / "deep" / "forecast.json"

            save_forecast(self.test_data, str(output_path))

            assert output_path.exists()

    def test_save_forecast_indentation(self):
        """Test that JSON is saved with proper indentation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "forecast.json"

            save_forecast(self.test_data, str(output_path))

            with open(output_path, "r") as f:
                content = f.read()

            # Check for indentation (should have spaces for nested objects)
            assert "  " in content  # At least 2-space indentation
            assert content.startswith("{")

    def test_save_forecast_unicode_handling(self):
        """Test that unicode characters are handled correctly."""
        test_data = {
            "location": "Paris, Île-de-France",
            "weather": "Ensoleillé ☀️",
            "data": self.test_data
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "forecast.json"

            save_forecast(test_data, str(output_path))

            with open(output_path, "r", encoding="utf-8") as f:
                saved_data = json.load(f)

            assert saved_data["forecast"]["location"] == "Paris, Île-de-France"
            assert "☀️" in saved_data["forecast"]["weather"]

    def test_save_forecast_overwrites_existing_file(self):
        """Test that existing file is overwritten."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "forecast.json"

            # Save first data
            first_data = {"temp": 10}
            save_forecast(first_data, str(output_path))

            # Save second data
            second_data = {"temp": 20}
            save_forecast(second_data, str(output_path))

            with open(output_path, "r") as f:
                saved_data = json.load(f)

            assert saved_data["forecast"]["temp"] == 20

    def test_save_forecast_complex_nested_structure(self):
        """Test saving complex nested data structures."""
        complex_data = {
            "weather": self.test_data,
            "metadata": {
                "source": "Open-Meteo",
                "version": 1,
                "nested": {
                    "deep": {
                        "value": [1, 2, 3, {"key": "value"}]
                    }
                }
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "forecast.json"

            save_forecast(complex_data, str(output_path))

            with open(output_path, "r") as f:
                saved_data = json.load(f)

            assert saved_data["forecast"]["metadata"]["nested"]["deep"]["value"] == [1, 2, 3, {"key": "value"}]


class TestIntegration:
    """Integration tests for weather module."""

    @patch('weather.requests.get')
    def test_forecast_workflow(self, mock_get):
        """Test complete workflow: fetch and save forecast."""
        valid_response_data = {
            "latitude": 48.85,
            "longitude": 2.35,
            "timezone": "Europe/Paris",
            "current_weather": {"temperature": 15.5},
            "hourly": {
                "time": ["2026-06-04T00:00"],
                "temperature_2m": [15.0],
                "precipitation": [0.0]
            }
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = valid_response_data
        mock_get.return_value = mock_response

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "forecast.json"

            # Fetch forecast
            forecast = get_forecast(48.85, 2.35, "Europe/Paris")

            # Save forecast
            save_forecast(forecast, str(output_path))

            # Verify saved data
            with open(output_path, "r") as f:
                saved_data = json.load(f)

            assert saved_data["forecast"]["current_weather"]["temperature"] == 15.5
            assert "timestamp" in saved_data
