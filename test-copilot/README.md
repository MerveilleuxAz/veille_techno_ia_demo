# Weather Module

A robust Python module for fetching weather forecast data from the Open-Meteo API with comprehensive error handling and logging.

## Features

- **`get_forecast(lat, lon, timezone)`**: Fetch current weather and 24-hour forecast data
- **`save_forecast(data, output_path)`**: Save forecast data to JSON with timestamp
- **Robust error handling**: Handles 422, 5xx errors, timeouts, and invalid coordinates
- **Validation**: Coordinate validation (-90/90 latitude, -180/180 longitude)
- **Logging**: Comprehensive logging for all operations
- **Timeout management**: Configurable 10-second timeout for API requests

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Fetch Forecast

```python
from weather import get_forecast, save_forecast

# Fetch weather for Paris
try:
    forecast = get_forecast(
        lat=48.85,
        lon=2.35,
        timezone="Europe/Paris",
        timeout=10
    )
    print(f"Current temperature: {forecast['current_weather']['temperature']}°C")
    
    # Save to file
    save_forecast(forecast, "paris_forecast.json")
except ValueError as e:
    print(f"Invalid coordinates: {e}")
except TimeoutError as e:
    print(f"Request timeout: {e}")
except Exception as e:
    print(f"Error: {e}")
```

### API Response Structure

```json
{
  "timestamp": "2026-06-04T12:30:45.123456",
  "forecast": {
    "current_weather": {
      "temperature": 15.5,
      "windspeed": 10.0,
      "time": "2026-06-04T12:00"
    },
    "hourly": {
      "time": ["2026-06-04T00:00", "2026-06-04T01:00", ...],
      "temperature_2m": [14.0, 13.5, ...],
      "precipitation": [0.0, 0.0, ...]
    }
  }
}
```

## Functions

### `get_forecast(lat, lon, timezone, timeout=10) -> Dict`

Fetch weather forecast from Open-Meteo API.

**Parameters:**
- `lat` (float): Latitude (-90 to 90)
- `lon` (float): Longitude (-180 to 180)
- `timezone` (str): Timezone string (e.g., "Europe/Paris")
- `timeout` (int): Request timeout in seconds (default: 10)

**Returns:**
- Dictionary with `current_weather` and hourly forecast data

**Raises:**
- `ValueError`: Invalid coordinates
- `requests.exceptions.Timeout`: Request timeout
- `requests.exceptions.HTTPError`: API errors (422, 5xx, etc.)

### `save_forecast(data, output_path) -> None`

Save forecast data to JSON file with ISO timestamp.

**Parameters:**
- `data` (Dict): Forecast data to save
- `output_path` (str): Path to output JSON file

**Raises:**
- `IOError`: File write errors
- `TypeError`: Non-serializable data

## Error Handling

The module handles:
- **422 Unprocessable Entity**: Invalid API parameters
- **5xx Server Errors**: API server issues
- **Timeout**: Requests exceeding timeout limit
- **Invalid Coordinates**: Latitude/longitude out of range
- **Connection Errors**: Network issues

## Logging

The module uses Python's logging module. Enable logging to see detailed operations:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('weather')
```

Log output includes:
- Forecast fetch requests
- Error conditions (422, 5xx, timeouts)
- File save operations
- Success confirmations

## Testing

Run the comprehensive test suite:

```bash
source venv/bin/activate
pytest test_weather.py -v
```

### Test Coverage

- ✅ Successful API responses
- ✅ 422 Unprocessable Entity handling
- ✅ 5xx Server error handling
- ✅ Request timeouts
- ✅ Invalid coordinate validation
- ✅ Boundary conditions (-90/90, -180/180)
- ✅ JSON file creation and formatting
- ✅ Timestamp generation
- ✅ Directory creation
- ✅ Unicode handling
- ✅ Integration workflow

**Coverage: 90%** (22/22 tests passing)

## Example Workflow

```python
from weather import get_forecast, save_forecast
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Fetch forecast
try:
    forecast = get_forecast(48.85, 2.35, "Europe/Paris")
    
    # Process data
    current_temp = forecast['current_weather']['temperature']
    hourly_temps = forecast['hourly']['temperature_2m']
    
    # Save for later use
    save_forecast(forecast, "forecast_backup.json")
    
    print(f"✓ Forecast saved successfully")
    
except ValueError as e:
    print(f"✗ Invalid input: {e}")
except TimeoutError as e:
    print(f"✗ Request failed: {e}")
```

## API Source

Data provided by Open-Meteo Free Weather API:
- **Endpoint**: `https://api.open-meteo.com/v1/forecast`
- **Documentation**: https://open-meteo.com/en/docs
- **License**: Open Data Commons Attribution License (ODC-By)
