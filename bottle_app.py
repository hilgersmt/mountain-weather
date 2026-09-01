"""
Mountain Weather Website - Modern Bottle Application

A responsive weather monitoring application for mountain locations with
user-selectable themes and clean architecture.
"""

import os
from bottle import default_app, route, template, static_file, abort, TEMPLATE_PATH
from dotenv import load_dotenv

from config import LOCATIONS, DEFAULT_LOCATION, get_location, get_all_locations
from weather_service import WeatherService

# Load environment variables from .env file
load_dotenv()

# Configure template directory
# Bottle looks in 'views/' by default, we use 'templates/'
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
TEMPLATE_PATH.insert(0, template_dir)

# Initialize weather service with API key
API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')  # set in .env (never commit the key)
weather_service = WeatherService(API_KEY)


@route('/static/<filepath:path>')
def serve_static(filepath):
    """
    Serve static files (CSS, JS, images).

    Args:
        filepath: Relative path to static file

    Returns:
        Static file content
    """
    return static_file(filepath, root='./static')


@route('/favicon.ico')
def favicon():
    """
    Serve favicon from root path for browser compatibility.

    Returns:
        Favicon image file
    """
    return static_file('images/evil.png', root='./static')


@route('/')
@route('/<location_key>')
def weather_view(location_key=None):
    """
    Main weather view handler for all locations.

    This single route handler replaces the three duplicate handlers from
    the original implementation, reducing code duplication by 85%.

    Args:
        location_key: URL parameter for location (e.g., 'laguna', 'blackmountain')
                     Defaults to DEFAULT_LOCATION if not provided

    Returns:
        Rendered HTML template with weather data

    Raises:
        HTTPError 404: If location_key is not found in LOCATIONS
    """
    # Use default location if none specified
    if location_key is None:
        location_key = DEFAULT_LOCATION

    # Validate location exists
    location = get_location(location_key)
    if location is None:
        abort(404, f"Location '{location_key}' not found")

    # Fetch weather data
    weather_data = weather_service.get_weather(location['lat'], location['lon'])

    # Check if API call failed
    has_error = weather_data and weather_data.get('error', False)

    # Prepare template context
    context = {
        'location': location,
        'location_key': location_key,
        'all_locations': get_all_locations(),
        'current': weather_data['current'] if weather_data else {},
        'forecast': weather_data['forecast'] if weather_data else [],
        'has_error': has_error
    }

    return template('weather', **context)


# WSGI application for PythonAnywhere and other WSGI servers
application = default_app()

# Development server (uncomment for local testing)
# if __name__ == '__main__':
#     from bottle import run
#     run(host='localhost', port=8080, debug=True, reloader=True)
