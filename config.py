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
