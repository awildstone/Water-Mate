import requests, json
from keys import MAPQUEST_KEY

BASE_URL = f'http://open.mapquestapi.com/geocoding/v1/address?key={MAPQUEST_KEY}'

class UserLocation:
    """A class instance for a User Location."""

    def __init__(self, city, state, country):
        self.city = city
        self.state = state
        self.country = country
    
    def get_coordinates(self):
        """Returns a Dict of latitude and longitude coordinates."""

        response = requests.get(BASE_URL, params={'location': [self.city, self.state, self.country]})

        #Our target accuracy level is A5 (City level): https://developer.mapquest.com/documentation/geocoding-api/quality-codes/
        #In order for the geocode pinpoint to meet criteria, the geocodeQualityCode must contain "A5", 
        # otherwise we will return an error message to the user to try again.
        print(response.json()['results'][0]['locations'][0]['geocodeQualityCode'])

        if 'A5' in response.json()['results'][0]['locations'][0]['geocodeQualityCode']:
            return(response.json()['results'][0]['locations'][0]['latLng'])