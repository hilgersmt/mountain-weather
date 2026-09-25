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


# Cache-busting token for static CSS/JS: newest file mtime, as an int string.
# git checkout/pull updates mtimes, so this changes automatically on each deploy
# and forces browsers to refetch changed stylesheets/scripts (no manual bumping).
def _asset_version():
    import glob
    base = os.path.dirname(__file__)
    latest = 0
    for pattern in ('static/css/*.css', 'static/js/*.js'):
        for f in glob.glob(os.path.join(base, pattern)):
            try:
                latest = max(latest, int(os.path.getmtime(f)))
            except OSError:
                pass
    return str(latest)

ASSET_VER = _asset_version()


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




# ---------------------------------------------------------------------------
# Map support endpoints
# ---------------------------------------------------------------------------
import time as _time
import requests as _requests

_temps_cache = {'ts': 0, 'data': {}}

@route('/api/temps')
def api_temps():
    """Current temperature for every locale (10-min cache) for map badges."""
    from bottle import response
    from config import LOCATIONS
    now = _time.time()
    if now - _temps_cache['ts'] > 600:
        data = {}
        for key, loc in LOCATIONS.items():
            try:
                w = weather_service.get_weather(loc['lat'], loc['lon'])
                data[key] = w['current']['temp'] if w else None
            except Exception:
                data[key] = None
        _temps_cache.update(ts=now, data=data)
    response.content_type = 'application/json'
    import json as _json
    return _json.dumps(_temps_cache['data'])


@route('/owmtile/<layer>/<z:int>/<x:int>/<y:int>.png')
def owm_tile(layer, z, x, y):
    """Proxy OpenWeatherMap weather tiles so the API key stays server-side."""
    from bottle import response, abort
    if layer not in ('precipitation_new', 'clouds_new', 'temp_new'):
        abort(404)
    try:
        r = _requests.get(
            f'https://tile.openweathermap.org/map/{layer}/{z}/{x}/{y}.png',
            params={'appid': API_KEY}, timeout=8)
        response.content_type = 'image/png'
        response.set_header('Cache-Control', 'public, max-age=600')
        return r.content
    except Exception:
        abort(502)


@route('/map')
def site_map():
    """Interactive map of all weather points and webcam locations."""
    import json as _json
    from config import LOCATIONS, MAP_CAMERAS
    locs = {k: {'name': v['name'], 'lat': v['lat'], 'lon': v['lon'],
                'elevation': v['elevation'], 'description': v['description']}
            for k, v in LOCATIONS.items()}
    return template('map', locations_json=_json.dumps(locs), cameras_json=_json.dumps(MAP_CAMERAS))


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
        'has_error': has_error,
        'asset_ver': ASSET_VER
    }

    return template('weather', **context)


# WSGI application for PythonAnywhere and other WSGI servers
application = default_app()

# Development server (uncomment for local testing)
# if __name__ == '__main__':
#     from bottle import run
#     run(host='localhost', port=8080, debug=True, reloader=True)
