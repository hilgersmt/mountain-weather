"""
Configuration file for mountain weather locations.

This module contains all location-specific data including coordinates,
webcam URLs, and forecast links. Webcam URLs are loaded from webcam_urls.md
for easier editing.
"""

import os
import re


def _load_webcam_urls():
    """
    Load webcam URLs from webcam_urls.md file.

    Parses the markdown file to extract static webcams and live streams
    for each location.

    Returns:
        Dictionary mapping location names to their webcam URLs
        Format: {
            'Mount Laguna': {
                'webcams': [...],
                'live_webcams': [...]
            }
        }
    """
    webcam_data = {}

    # Get the path to webcam_urls.md
    config_dir = os.path.dirname(__file__)
    webcam_file = os.path.join(config_dir, 'webcam_urls.md')

    # If file doesn't exist, return empty data
    if not os.path.exists(webcam_file):
        return webcam_data

    try:
        with open(webcam_file, 'r') as f:
            lines = f.readlines()

        current_location = None
        current_section = None
        in_html_comment = False

        for line in lines:
            line = line.rstrip()
            stripped_line = line.strip()

            # Skip empty lines
            if not stripped_line:
                continue

            # Handle HTML comments (can span multiple lines)
            if '<!--' in line:
                in_html_comment = True
            if in_html_comment:
                if '-->' in line:
                    in_html_comment = False
                continue

            # Match location headers (## Location Name) - check BEFORE comment check
            location_match = re.match(r'^##\s+(.+)$', line)
            if location_match:
                current_location = location_match.group(1).strip()
                webcam_data[current_location] = {
                    'webcams': [],
                    'live_webcams': []
                }
                current_section = None
                continue

            # Match section headers (### Current Views or ### Live Streams) - check BEFORE comment check
            section_match = re.match(r'^###\s+(.+)$', line)
            if section_match and current_location:
                section_name = section_match.group(1).strip()
                if 'current views' in section_name.lower():
                    current_section = 'webcams'
                elif 'live streams' in section_name.lower():
                    current_section = 'live_webcams'
                continue

            # Skip lines starting with # (single # = comment line)
            # This check comes AFTER ## and ### checks
            if stripped_line.startswith('#'):
                continue

            # Match URLs (lines starting with "- " followed by URL)
            # This will NOT match lines like "OFFLINE - https://..." because
            # the regex requires the line to START with "-"
            url_match = re.match(r'^-\s+(https?://\S+)$', line)
            if url_match and current_location and current_section:
                url = url_match.group(1).strip()
                webcam_data[current_location][current_section].append(url)

    except Exception as e:
        print(f"Warning: Could not load webcam URLs from {webcam_file}: {e}")

    return webcam_data


# Load webcam URLs from markdown file
_WEBCAM_URLS = _load_webcam_urls()

LOCATIONS = {
    'laguna': {
        'name': 'Mount Laguna',
        'lat': 32.8737605,
        'lon': -116.4248798,
        'elevation': '6000 ft',
        'description': 'Laguna Mountain Recreation Area in Cleveland National Forest',
        'forecast_link': 'https://www.wunderground.com/forecast/us/ca/mount-laguna?cm_ven=localwx_10day',
        'webcams': _WEBCAM_URLS.get('Mount Laguna', {}).get('webcams', []),
        'live_webcams': _WEBCAM_URLS.get('Mount Laguna', {}).get('live_webcams', [])
    },

    'blackmountain': {
        'name': 'Black Mountain',
        'lat': 32.9768799,
        'lon': -117.1198936,
        'elevation': '1555 ft',
        'description': 'Black Mountain Open Space Park in San Diego',
        'forecast_link': 'https://www.wunderground.com/forecast/us/ca/san-diego/KCASANDI424?cm_ven=localwx_10day',
        'webcams': _WEBCAM_URLS.get('Black Mountain', {}).get('webcams', []),
        'live_webcams': _WEBCAM_URLS.get('Black Mountain', {}).get('live_webcams', [])
    },

    'idyllwild': {
        'name': 'Idyllwild',
        'lat': 33.7598072,
        'lon': -116.7027706,
        'elevation': '5400 ft',
        'description': 'Best mountain town in the world',
        'forecast_link': 'https://www.wunderground.com/forecast/us/ca/idyllwild/KCAIDYLL14?cm_ven=localwx_10day',
        'webcams': _WEBCAM_URLS.get('Idyllwild', {}).get('webcams', []),
        'live_webcams': _WEBCAM_URLS.get('Idyllwild', {}).get('live_webcams', [])
    },
    'woodson': {
        'name': 'Mount Woodson',
        'lat': 33.0076,
        'lon': -116.9715,
        'elevation': '2894 ft',
        'description': 'Mount Woodson and the Sycamore Canyon trails above Poway',
        'forecast_link': 'https://www.wunderground.com/forecast/us/ca/poway?cm_ven=localwx_10day',
        'webcams': _WEBCAM_URLS.get('Mount Woodson', {}).get('webcams', []),
        'live_webcams': _WEBCAM_URLS.get('Mount Woodson', {}).get('live_webcams', [])
    },

    'cowles': {
        'name': 'Cowles Mountain',
        'lat': 32.8087,
        'lon': -117.0303,
        'elevation': '1593 ft',
        'description': 'Mission Trails Regional Park and the highest point in the city of San Diego',
        'forecast_link': 'https://www.wunderground.com/forecast/us/ca/san-diego?cm_ven=localwx_10day',
        'webcams': _WEBCAM_URLS.get('Cowles Mountain', {}).get('webcams', []),
        'live_webcams': _WEBCAM_URLS.get('Cowles Mountain', {}).get('live_webcams', [])
    },

    'doublepeak': {
        'name': 'Double Peak',
        'lat': 33.1030,
        'lon': -117.1745,
        'elevation': '1644 ft',
        'description': 'Double Peak above San Elijo Hills and the La Costa trail network',
        'forecast_link': 'https://www.wunderground.com/forecast/us/ca/san-marcos?cm_ven=localwx_10day',
        'webcams': _WEBCAM_URLS.get('Double Peak', {}).get('webcams', []),
        'live_webcams': _WEBCAM_URLS.get('Double Peak', {}).get('live_webcams', [])
    },

    'daleyranch': {
        'name': 'Daley Ranch',
        'lat': 33.1700,
        'lon': -117.0550,
        'elevation': '1983 ft',
        'description': 'Daley Ranch preserve above Escondido, up to Stanley Peak',
        'forecast_link': 'https://www.wunderground.com/forecast/us/ca/escondido?cm_ven=localwx_10day',
        'webcams': _WEBCAM_URLS.get('Daley Ranch', {}).get('webcams', []),
        'live_webcams': _WEBCAM_URLS.get('Daley Ranch', {}).get('live_webcams', [])
    },

    'lakehodges': {
        'name': 'Lake Hodges',
        'lat': 33.0520,
        'lon': -117.0692,
        'elevation': '330 ft',
        'description': 'Lake Hodges, Raptor Ridge, and the San Pasqual valley trails',
        'forecast_link': 'https://www.wunderground.com/forecast/us/ca/escondido?cm_ven=localwx_10day',
        'webcams': _WEBCAM_URLS.get('Lake Hodges', {}).get('webcams', []),
        'live_webcams': _WEBCAM_URLS.get('Lake Hodges', {}).get('live_webcams', [])
    },
    'jamul': {
        'name': 'Jamul',
        'lat': 32.7396,
        'lon': -116.9124,
        'elevation': '1000 ft',
        'description': 'Jamul and Lyons Valley backcountry, under San Miguel and Lyons Peak',
        'forecast_link': 'https://www.wunderground.com/forecast/us/ca/jamul?cm_ven=localwx_10day',
        'webcams': _WEBCAM_URLS.get('Jamul', {}).get('webcams', []),
        'live_webcams': _WEBCAM_URLS.get('Jamul', {}).get('live_webcams', [])
    },

    'bend': {
        'name': 'Bend, OR',
        'lat': 44.0430,
        'lon': -121.3730,
        'elevation': '3900 ft',
        'description': "Phil's Trails and central Oregon riding, with Mt. Bachelor cams",
        'forecast_link': 'https://www.wunderground.com/forecast/us/or/bend?cm_ven=localwx_10day',
        'webcams': _WEBCAM_URLS.get('Bend', {}).get('webcams', []),
        'live_webcams': _WEBCAM_URLS.get('Bend', {}).get('live_webcams', [])
    }
}



# Default location when accessing root URL
DEFAULT_LOCATION = 'laguna'

def get_location(location_key):
    """
    Get location configuration by key.

    Args:
        location_key: String key for the location (e.g., 'laguna', 'blackmountain')

    Returns:
        Dictionary containing location data, or None if not found
    """
    return LOCATIONS.get(location_key)

def get_all_locations():
    """
    Get all available locations.

    Returns:
        Dictionary of all location configurations
    """
    return LOCATIONS


# Camera locations for the /map page (name, lat, lon, image url)
MAP_CAMERAS = [
  {
    "name": "Mount Laguna Observatory, Laguna Mountains",
    "lat": 32.83989,
    "lon": -116.42658,
    "url": "https://cdn.hpwren.ucsd.edu/RT/mlo-n-axis.jpg"
  },
  {
    "name": "Mount Woodson CAL FIRE, west of Ramona",
    "lat": 33.00872,
    "lon": -116.97101,
    "url": "https://cdn.hpwren.ucsd.edu/RT/wc-axis.jpg"
  },
  {
    "name": "RAAB",
    "lat": 33.04032,
    "lon": -116.91175,
    "url": "https://cdn.hpwren.ucsd.edu/RT/raab-axis.jpg"
  },
  {
    "name": "Cowles Mountain",
    "lat": 32.81359,
    "lon": -117.03233,
    "url": "https://cdn.hpwren.ucsd.edu/RT/cowles-axis.jpg"
  },
  {
    "name": "San Diego State University",
    "lat": 32.77661,
    "lon": -117.07312,
    "url": "https://cdn.hpwren.ucsd.edu/RT/sdsu-chappycam.jpg"
  },
  {
    "name": "Coronado Hills, Harmony Grove",
    "lat": 33.11063,
    "lon": -117.15296,
    "url": "https://cdn.hpwren.ucsd.edu/RT/ch-n-axis.jpg"
  },
  {
    "name": "Rincon Del Diablo, Escondido",
    "lat": 33.09388,
    "lon": -117.12105,
    "url": "https://cdn.hpwren.ucsd.edu/RT/rdd-n-axis.jpg"
  },
  {
    "name": "Lake Wohlford Airport, northeast of Escondido",
    "lat": 33.17469,
    "lon": -117.00441,
    "url": "https://cdn.hpwren.ucsd.edu/RT/wlfd-n-axis.jpg"
  },
  {
    "name": "San Miguel, west of Jamul",
    "lat": 32.69686,
    "lon": -116.93612,
    "url": "https://cdn.hpwren.ucsd.edu/RT/sm-n-axis.jpg"
  },
  {
    "name": "Lyons Peak, east of Jamul",
    "lat": 32.70153,
    "lon": -116.76457,
    "url": "https://cdn.hpwren.ucsd.edu/RT/lp-n-axis.jpg"
  },
  {
    "name": "Marion Ridge, north of Pine Cove-Idyllwild",
    "lat": 33.76528,
    "lon": -116.73164,
    "url": "https://cdn.hpwren.ucsd.edu/RT/marion-n-axis.jpg"
  },
  {
    "name": "Idyllwild Pine Cove",
    "lat": 33.765,
    "lon": -116.732,
    "url": "https://cdn.hpwren.ucsd.edu/RT/idlwld-se-delphire.jpg"
  },
  {
    "name": "Black Mountain Lookout, San Jacinto Mountains",
    "lat": 33.82422,
    "lon": -116.75763,
    "url": "https://cdn.hpwren.ucsd.edu/RT/blkrc-n-axis.jpg"
  },
  {
    "name": "Black Mountain, Rancho Penasquitos",
    "lat": 32.98143,
    "lon": -117.1165,
    "url": "https://cdn.hpwren.ucsd.edu/RT/bl2-axis.jpg"
  },
  {
    "name": "Monument Peak, Laguna Mountains",
    "lat": 32.89225,
    "lon": -116.42087,
    "url": "https://cdn.hpwren.ucsd.edu/RTS/mp-n-axis-640.jpg"
  },
  {
    "name": "Double Peak 2",
    "lat": 33.109219,
    "lon": -117.178119,
    "url": "https://cameras.alertcalifornia.org/public-camera-data/Axis-DoublePeak2/latest-frame.jpg"
  },
  {
    "name": "La Costa 2",
    "lat": 33.105349,
    "lon": -117.235328,
    "url": "https://cameras.alertcalifornia.org/public-camera-data/Axis-LaCosta2/latest-frame.jpg"
  },
  {
    "name": "SD Safari Park West 2",
    "lat": 33.106305,
    "lon": -116.987591,
    "url": "https://cameras.alertcalifornia.org/public-camera-data/Axis-SafariParkWest2/latest-frame.jpg"
  },
  {
    "name": "Idyllwild 2",
    "lat": 33.725632,
    "lon": -116.750679,
    "url": "https://cameras.alertcalifornia.org/public-camera-data/Axis-Idyllwild2/latest-frame.jpg"
  },
  {
    "name": "Crest 2",
    "lat": 32.8046,
    "lon": -116.876999,
    "url": "https://cameras.alertcalifornia.org/public-camera-data/Axis-Crest2/latest-frame.jpg"
  },
  {
    "name": "Mt. Bachelor Summit",
    "lat": 43.9793,
    "lon": -121.6885,
    "url": "https://api.mtbachelor.com/api/v1/cams/mtn/8"
  },
  {
    "name": "Mt. Bachelor Mid-Mountain",
    "lat": 43.99,
    "lon": -121.675,
    "url": "https://api.mtbachelor.com/api/v1/cams/mtn/12"
  },
  {
    "name": "Mt. Bachelor Sunrise Base",
    "lat": 43.995,
    "lon": -121.66,
    "url": "https://api.mtbachelor.com/api/v1/cams/mtn/5"
  }
]
