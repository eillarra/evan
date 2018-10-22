import requests

from os import environ
from typing import Tuple


def geocode(address) -> Tuple[float, float]:
    """
    Given an text address it requests the Google Geocoding API to return a (latitude, longitude) tuple.
    Help: https://developers.google.com/maps/documentation/geocoding/start
    """
    payload = {
        'address': address,
        'key': environ.get('GOOGLE_GEOCODING_API_KEY', ''),
    }
    r = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params=payload)
    res = r.json()

    try:
        location = res['results'][0]['geometry']['location']
        return (location['lat'], location['lng'])
    except Exception:
        return (None, None)
