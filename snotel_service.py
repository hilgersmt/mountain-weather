"""
SNOTEL service — current snowpack readings from the USDA NRCS
Air & Water Database (AWDB) REST API for a given station triplet.

Used to show real snow-on-the-ground for high-elevation locations
(e.g. the Mt. Bachelor tiles) alongside the OpenWeatherMap forecast,
since the forecast alone can't tell you what's actually lying at the
trailhead. Nearest real-time station to Bachelor is Irish Taylor
(545:OR:SNTL, 5,540 ft); there is no telemetered Dutchman Flat sensor.
"""

import logging
from datetime import datetime, timedelta

import requests

logger = logging.getLogger(__name__)

AWDB_URL = 'https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/data'
TIMEOUT = 8  # seconds

# AWDB element code -> friendly key used in the template
_ELEMENT_KEYS = {
    'SNWD': 'snow_depth',   # snow depth, inches
    'WTEQ': 'swe',          # snow-water equivalent, inches
    'TOBS': 'temp',         # observed air temp, deg F
}


def get_snotel(triplet, elements=('SNWD', 'WTEQ', 'TOBS')):
    """
    Fetch the most recent daily SNOTEL readings for a station triplet
    such as '545:OR:SNTL'.

    Returns a dict like
        {'snow_depth': 0, 'swe': 0.0, 'temp': 38.5, 'date': '2026-09-29'}
    (elements that are missing/None are omitted), or None on any failure.
    """
    end = datetime.now().date()
    begin = end - timedelta(days=10)
    params = {
        'stationTriplets': triplet,
        'elements': ','.join(elements),
        'duration': 'DAILY',
        'beginDate': begin.isoformat(),
        'endDate': end.isoformat(),
    }
    try:
        resp = requests.get(AWDB_URL, params=params, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()
    except (requests.exceptions.RequestException, ValueError) as e:
        logger.error(f"SNOTEL fetch failed for {triplet}: {e}")
        return None

    if not data:
        return None

    result = {}
    latest_date = None
    for element in data[0].get('data', []):
        code = element.get('stationElement', {}).get('elementCode')
        out_key = _ELEMENT_KEYS.get(code)
        if not out_key:
            continue
        # Values are oldest-first; take the newest non-null reading.
        for value in reversed(element.get('values', [])):
            if value.get('value') is not None:
                result[out_key] = value['value']
                date = value.get('date')
                if date and (latest_date is None or date > latest_date):
                    latest_date = date
                break

    if not result:
        return None
    if latest_date:
        result['date'] = latest_date
    return result
