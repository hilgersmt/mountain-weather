"""
Mountain Weather Website - Modern Bottle Application

A responsive weather monitoring application for mountain locations with
user-selectable themes and clean architecture.
"""

import json
import os
from bottle import default_app, route, hook, request, redirect, template, static_file, abort, TEMPLATE_PATH
from dotenv import load_dotenv

from config import (LOCATIONS, DEFAULT_LOCATION, NEAREST_ALIASES, CANONICAL_ORIGIN,
                    REDIRECT_HOSTS, get_location, get_all_locations)
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

# Data for the client-side "Start page" preference (static/js/start-page.js):
# the site default, every location's coordinates for the nearest-to-me option,
# and the band aliases. Embedded in the page as JSON; '</' is escaped so the
# payload can't terminate its <script> element.
START_PAGE_JSON = json.dumps({
    'default': DEFAULT_LOCATION,
    'aliases': NEAREST_ALIASES,
    'locations': [{'key': k, 'name': v['name'], 'lat': v['lat'], 'lon': v['lon']}
                  for k, v in LOCATIONS.items()],
}).replace('</', '<\\/')


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


@hook('before_request')
def redirect_to_canonical_host():
    """Send requests for an old host (e.g. hilgersmt.pythonanywhere.com) to the
    same path and query on CANONICAL_ORIGIN, permanently."""
    host = request.environ.get('HTTP_HOST', '').split(':')[0].lower()
    if host in REDIRECT_HOSTS:
        target = CANONICAL_ORIGIN + request.environ.get('PATH_INFO', '/')
        if request.query_string:
            target += '?' + request.query_string
        redirect(target, 301)


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

# SNOTEL readings change once a day; cache per station triplet for an hour.
_snotel_cache = {}  # triplet -> {'ts': float, 'data': dict|None}


def _get_snotel_cached(triplet):
    """Fetch a SNOTEL reading with a 1-hour cache; never raises."""
    from snotel_service import get_snotel
    now = _time.time()
    cached = _snotel_cache.get(triplet)
    if cached and now - cached['ts'] < 3600:
        return cached['data']
    try:
        data = get_snotel(triplet)
    except Exception:
        data = None
    _snotel_cache[triplet] = {'ts': now, 'data': data}
    return data

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


@route('/privacy')
def privacy():
    """Privacy policy. Also serves as the policy URL for the owner's personal
    Google OAuth app (home-nest: Nest thermostat -> Homebridge), which Google
    requires before an OAuth app can leave Testing mode."""
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Privacy - chickenbaby.org</title>
<style>body{font:16px/1.55 -apple-system,system-ui,sans-serif;max-width:40rem;margin:2rem auto;padding:0 1rem;color:#222}
@media (prefers-color-scheme:dark){body{background:#111;color:#ddd}a{color:#8ab4f8}}</style></head><body>
<h1>Privacy</h1>
<p><b>This website.</b> chickenbaby.org shows mountain weather and public webcams. It has no accounts and
sets no tracking cookies. If you choose "nearest location", your device's position is used in your browser
only and is not sent to or stored by this site. Standard web-server logs (IP address, page requested) are kept
by the hosting provider for operations only.</p>
<p><b>home-nest (personal Google sign-in app).</b> "home-nest" is a private, single-household home-automation
integration operated by the site owner for their own home. It uses Google's Smart Device Management API to read
and adjust the owner's own Nest thermostat from the owner's home server. It is not offered to the public. Data
received from Google (thermostat temperature, setpoints, mode, humidity) is used only to display and control that
thermostat, stays on the owner's home server, and is never sold, shared, or used for advertising. Access can be
revoked at any time at <a href="https://myaccount.google.com/permissions">myaccount.google.com/permissions</a>.</p>
<p>Contact: hilgersmt@gmail.com</p>
<p><a href="/">&larr; Back to weather</a></p>
</body></html>"""


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

    # Optional live snowpack reading for high-elevation locations (e.g. Bachelor).
    snotel = None
    snotel_cfg = location.get('snotel')
    if snotel_cfg:
        reading = _get_snotel_cached(snotel_cfg['triplet'])
        if reading:
            snotel = dict(reading)
            snotel['name'] = snotel_cfg.get('name', 'SNOTEL')
            snotel['station_elevation'] = snotel_cfg.get('elevation', '')

    # Prepare template context
    context = {
        'location': location,
        'location_key': location_key,
        'all_locations': get_all_locations(),
        'current': weather_data['current'] if weather_data else {},
        'forecast': weather_data['forecast'] if weather_data else [],
        'snotel': snotel,
        'has_error': has_error,
        'asset_ver': ASSET_VER,
        'start_page_json': START_PAGE_JSON,
        'default_location': DEFAULT_LOCATION
    }

    return template('weather', **context)


# WSGI application for PythonAnywhere and other WSGI servers
application = default_app()

# Development server (uncomment for local testing)
# if __name__ == '__main__':
#     from bottle import run
#     run(host='localhost', port=8080, debug=True, reloader=True)
