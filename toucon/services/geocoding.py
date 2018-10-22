import requests


def geocode(address):
    """
    Given an text address it requests the Google Geocoding API to return a (latiutude, longitude) tuple.
    Help: https://developers.google.com/maps/documentation/geocoding/start
    """
    payload = {
        'address': address,
        'key': 'AIzaSyBFx2atP-hgXqq3ulRYDg9XFqfrRlqR4Q0	',
    }
    r = requests.get('https://maps.googleapis.com/maps/api/geocode/json', params=payload)
    res = r.json()

    try:
        location = res['results'][0]['geometry']['location']
        return (location['lat'], location['lng'])
    except Exception as e:
        return (None, None)
