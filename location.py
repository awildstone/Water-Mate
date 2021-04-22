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

        # print(response.json()['results'][0]['locations'])
        # print(len(response.json()['results'][0]['locations']))
        # #If mapquest cannot find the location based on the input then the json response will include more than one location in the response, or 0 location results in the response. In these cases, we will assume there was an error and have the user try again.

        return(response.json()['results'][0]['locations'][0]['latLng'])