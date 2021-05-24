import os
from dotenv import load_dotenv
import requests, json

load_dotenv()  # take environment variables from .env

MAPQUEST_KEY = os.getenv('MAPQUEST_KEY')
BASE_URL = f'http://open.mapquestapi.com/geocoding/v1/address?key={MAPQUEST_KEY}'
CITY_LEVEL = 'A5';

class UserLocation:
    """A class instance for a User Location."""

    def __init__(self, city, state=None, country=None):
        self.city = city
        self.state = state
        self.country = country
    
    def _get_location(self):
        """Returns the location data based on the provided user input."""

        if (self.city and self.state and self.country):
            return f'{self.city}, {self.state}, {self.country}'

        if (self.city and self.state):
            return f'{self.city}, {self.state}'
        
        if (self.city and self.country):
            return f'{self.city}, {self.country}'
    
    def get_coordinates(self):
        """Returns a Dict of latitude and longitude coordinates.
        Our target accuracy level is A5 (City level): https://developer.mapquest.com/documentation/geocoding-api/quality-codes/

        In order for the geocode pinpoint to meet criteria, the geocodeQualityCode must contain "A5",
        otherwise we will return an error message to the user to try again.

        Example API response:

        {
        "info": {
            "statuscode": 0,
            "copyright": {
            "text": "© 2018 MapQuest, Inc.",
            "imageUrl": "http://api.mqcdn.com/res/mqlogo.gif",
            "imageAltText": "© 2018 MapQuest, Inc."
        },
        "messages": []
        },
            "options": {
            "maxResults": -1,
            "thumbMaps": true,
            "ignoreLatLngInput": false
        },
        "results": [
            {
            "providedLocation": {
                "location": "Washington,DC"
            },
            "locations": [
                {
                "street": "",
                "adminArea6": "",
                "adminArea6Type": "Neighborhood",
                "adminArea5": "Washington",
                "adminArea5Type": "City",
                "adminArea4": "District of Columbia",
                "adminArea4Type": "County",
                "adminArea3": "DC",
                "adminArea3Type": "State",
                "adminArea1": "US",
                "adminArea1Type": "Country",
                "postalCode": "",
                "geocodeQualityCode": "A5XAX",
                "geocodeQuality": "CITY",
                "dragPoint": false,
                "sideOfStreet": "N",
                "linkId": "282772166",
                "unknownInput": "",
                "type": "s",
                "latLng": {
                    "lat": 38.892062,
                    "lng": -77.019912
                },
                "displayLatLng": {
                    "lat": 38.892062,
                    "lng": -77.019912
                },
                "mapUrl": "http://www.mapquestapi.com/staticmap/v4/getmap?key=KEY&type=map&size=225,160&pois=purple-1,38.892062,-77.019912,0,0,|&center=38.892062,-77.019912&zoom=12&rand=306744981"
                }
            ]
            }
        ]
        }
        
        """

        if (self.city and not self.state and not self.country):
            return
        
        response = requests.get(BASE_URL, params={'location': self._get_location()})
        first_result = response.json()['results'][0]['locations'][0]

        if CITY_LEVEL in (first_result['geocodeQualityCode']):
            return first_result['latLng']