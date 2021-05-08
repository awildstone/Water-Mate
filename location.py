import os
import requests, json
# from keys import MAPQUEST_KEY #for production testing

MAPQUEST_KEY = os.getenv('MAPQUEST_KEY')

BASE_URL = f'http://open.mapquestapi.com/geocoding/v1/address?key={MAPQUEST_KEY}'

class UserLocation:
    """A class instance for a User Location."""

    def __init__(self, city, state=None, country=None):
        self.city = city
        self.state = state
        self.country = country
    
    def get_coordinates(self):
        """Returns a Dict of latitude and longitude coordinates.
        Our target accuracy level is A5 (City level): https://developer.mapquest.com/documentation/geocoding-api/quality-codes/

        In order for the geocode pinpoint to meet criteria, the geocodeQualityCode must contain "A5",
        otherwise we will return an error message to the user to try again."""

        if (self.city and not self.state and not self.country):
            return
            
        if (self.city and self.state and self.country):
            response = requests.get(BASE_URL, params={'location': f'{self.city},{self.state},{self.country}'})
        
        if (self.city and self.state):
            response = requests.get(BASE_URL, params={'location': f'{self.city},{self.state}'})
        
        if (self.city and self.country):
            response = requests.get(BASE_URL, params={'location': f'{self.city},{self.country}'})

        if 'A5' in (response.json()['results'][0]['locations'][0]['geocodeQualityCode']):
            return response.json()['results'][0]['locations'][0]['latLng']