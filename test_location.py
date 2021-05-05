"""Location Tests"""

#FLASK_ENV=production python -m unittest test_location.py

from unittest import TestCase
import requests, json
from keys import MAPQUEST_KEY
from location import UserLocation

class TestUserLocation(TestCase):
    """Class to test the User Location feature."""

    def setUp(self):
        """Setup UserLocation Objects."""

        seattle = UserLocation(city='Seattle', state='WA', country='USA')
        paris = UserLocation(city='Paris', country='France')
        queenstown = UserLocation(city='Queenstown', country='NZ')
        victoria = UserLocation(city='Victoria', state='BC', country='Canada')
        bejing = UserLocation(city='bejing', country='China')
        vague_city = UserLocation(city='Springfield')
        fake_city = UserLocation(city='Faker', country='Mexico')

        self.seattle = seattle
        self.paris = paris
        self.queenstown = queenstown
        self.victoria = victoria
        self.bejing = bejing
        self.vague_city = vague_city
        self.fake_city = fake_city


    def test_create_user_location(self):
        """Test creating new user locations."""

        self.assertIsInstance(self.seattle, UserLocation)
        self.assertIsInstance(self.paris, UserLocation)
        self.assertIsInstance(self.queenstown, UserLocation)
        self.assertIsInstance(self.victoria, UserLocation)
        self.assertIsInstance(self.bejing, UserLocation)
    
    def test_get_location_data(self):
        """Test getting the geolocation data."""

        self.assertEqual(self.seattle.get_coordinates(), {'lat': 47.603832, 'lng': -122.330062})
        self.assertEqual(self.paris.get_coordinates(), {'lat': 48.85661, 'lng': 2.351499})
        self.assertEqual(self.queenstown.get_coordinates(), {'lat': -45.03172, 'lng': 168.66081})
        self.assertEqual(self.victoria.get_coordinates(), {'lat': 48.428318, 'lng': -123.364953})
        self.assertEqual(self.bejing.get_coordinates(), {'lat': 39.905963, 'lng': 116.391248})

        self.assertIsNone(self.vague_city.get_coordinates())
        self.assertIsNone(self.fake_city.get_coordinates())