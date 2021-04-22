import requests, json
from keys import MAPQUEST_KEY

BASE_URL = f'http://open.mapquestapi.com/geocoding/v1/address?key={MAPQUEST_KEY}'

class UserLocation:
    """A class instance for a User Location."""

    def __init__(self, city, state):
        self.city = city
        self.state = state
    
    def get_coordinates(self):
        """Returns a Dict of latitude and longitude coordinates."""

        response = requests.get(BASE_URL, params={'location': [self.city, self.state]})

        return(response.json()['results'][0]['locations'][0]['latLng'])