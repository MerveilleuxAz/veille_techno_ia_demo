#!/usr/bin/env python3
"""
Example script demonstrating weather module usage.
"""

import logging
from datetime import datetime
from weather import get_forecast, save_forecast

# Configure logging to see detailed operations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


def main():
    """Main example function."""
    
    # Example coordinates: Paris, France
    lat, lon = 48.85, 2.35
    timezone = "Europe/Paris"
    
    print(f"\n{'='*60}")
    print(f"Weather Forecast Fetcher - Example")
    print(f"{'='*60}")
    print(f"Location: Paris, France ({lat}°N, {lon}°E)")
    print(f"Timezone: {timezone}")
    print(f"{'='*60}\n")
    
    try:
        # Fetch forecast
        print("📡 Fetching forecast from Open-Meteo API...")
        forecast = get_forecast(lat, lon, timezone, timeout=10)
        
        # Extract current weather
        current = forecast['current_weather']
        print(f"\n🌡️  Current Weather:")
        print(f"   Temperature: {current['temperature']}°C")
        print(f"   Wind Speed: {current['windspeed']} km/h")
        print(f"   Time: {current['time']}")
        
        # Extract hourly data
        hourly = forecast['hourly']
        temps = hourly['temperature_2m']
        precip = hourly['precipitation']
        
        print(f"\n📊 24-Hour Forecast:")
        print(f"   Hours available: {len(temps)}")
        print(f"   Avg temperature: {sum(temps)/len(temps):.1f}°C")
        print(f"   Min temperature: {min(temps):.1f}°C")
        print(f"   Max temperature: {max(temps):.1f}°C")
        print(f"   Total precipitation: {sum(precip):.1f} mm")
        
        # Save forecast to file
        output_file = "weather_forecast.json"
        print(f"\n💾 Saving forecast to {output_file}...")
        save_forecast(forecast, output_file)
        
        print(f"\n✅ Success! Forecast saved and displayed.\n")
        
    except ValueError as e:
        print(f"❌ Invalid input: {e}\n")
        return False
        
    except TimeoutError as e:
        print(f"❌ Request timeout: {e}\n")
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}\n")
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
