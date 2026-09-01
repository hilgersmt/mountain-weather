"""
Weather service module for fetching and processing weather data.

This module provides a clean interface to the OpenWeatherMap API with
proper error handling, timeouts, and fallback data.
"""

import requests
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WeatherService:
    """Service for fetching weather data from OpenWeatherMap API."""

    BASE_URL = 'https://api.openweathermap.org/data/3.0/onecall'
    ICON_BASE_URL = 'https://openweathermap.org/img/wn/'
    TIMEOUT = 10  # seconds

    def __init__(self, api_key):
        """
        Initialize the weather service.

        Args:
            api_key: OpenWeatherMap API key
        """
        self.api_key = api_key

    def get_weather(self, lat, lon):
        """
        Fetch weather data for given coordinates.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dictionary containing current weather and forecast data, or None on error

        Example return structure:
            {
                'current': {
                    'temp': '65.3',
                    'feels_like': '63.2',
                    'wind_speed': '5.8',
                    'visibility': '10.0',
                    'icon_url': 'https://...'
                },
                'forecast': [
                    {
                        'date': 'Mon 01/20',
                        'temp_max': '68',
                        'temp_min': '52',
                        'icon_url': 'https://...'
                    },
                    ...
                ]
            }
        """
        try:
            # Build API request
            params = {
                'lat': lat,
                'lon': lon,
                'units': 'imperial',
                'appid': self.api_key
            }

            # Make API call with timeout
            logger.info(f"Fetching weather data for lat={lat}, lon={lon}")
            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=self.TIMEOUT
            )

            # Check for HTTP errors
            response.raise_for_status()

            # Parse response
            data = response.json()
            return self._parse_weather_data(data)

        except requests.exceptions.Timeout:
            logger.error(f"Timeout fetching weather data for lat={lat}, lon={lon}")
            return self._get_fallback_data()

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error fetching weather: {e}")
            return self._get_fallback_data()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching weather data: {e}")
            return self._get_fallback_data()

        except (KeyError, ValueError) as e:
            logger.error(f"Error parsing weather data: {e}")
            return self._get_fallback_data()

    def _parse_weather_data(self, data):
        """
        Parse raw API response into simplified format.

        Args:
            data: Raw JSON response from OpenWeatherMap API

        Returns:
            Parsed weather data dictionary
        """
        # Parse current weather
        current = data['current']
        current_weather = {
            'temp': str(round(float(current['temp']), 1)),
            'feels_like': str(round(float(current['feels_like']), 1)),
            'wind_speed': str(round(float(current.get('wind_speed', 0)), 1)),
            'visibility': str(round(float(current.get('visibility', 0)) / 1609.34, 1)),  # Convert meters to miles
            'icon_url': self._get_icon_url(current['weather'][0]['icon'])
        }

        # Parse forecast (7 days)
        forecast = []
        for day in data['daily'][:7]:
            forecast.append({
                'date': self._format_date(day['dt']),
                'temp_max': str(round(float(day['temp']['max']))),
                'temp_min': str(round(float(day['temp']['min']))),
                'icon_url': self._get_icon_url(day['weather'][0]['icon'])
            })

        return {
            'current': current_weather,
            'forecast': forecast
        }

    def _get_icon_url(self, icon_code):
        """
        Build icon URL from icon code.

        Args:
            icon_code: OpenWeatherMap icon code (e.g., '01d')

        Returns:
            Full URL to weather icon
        """
        return f'{self.ICON_BASE_URL}{icon_code}@2x.png'

    def _format_date(self, timestamp):
        """
        Format Unix timestamp to readable date.

        Args:
            timestamp: Unix timestamp

        Returns:
            Formatted date string (e.g., 'Mon 01/20')
        """
        return datetime.fromtimestamp(timestamp).strftime("%a %m/%d")

    def _get_fallback_data(self):
        """
        Return fallback data when API fails.

        Returns:
            Basic fallback weather data
        """
        return {
            'current': {
                'temp': '--',
                'feels_like': '--',
                'wind_speed': '--',
                'visibility': '--',
                'icon_url': self._get_icon_url('01d')  # Default sunny icon
            },
            'forecast': [
                {
                    'date': self._format_date(1700000000 + (i * 86400)),
                    'temp_max': '--',
                    'temp_min': '--',
                    'icon_url': self._get_icon_url('01d')
                }
                for i in range(7)
            ],
            'error': True
        }
