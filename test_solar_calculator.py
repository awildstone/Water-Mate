"""Solar Calculator Tests."""

#FLASK_ENV=production python -m unittest test_solar_calculator.py

from unittest import TestCase
from datetime import date, datetime, timedelta, timezone
from dateutil import tz
import pytz
from tzlocal import get_localzone
from solar_calculator import SolarCalculator

BASE_URL = 'https://api.sunrise-sunset.org/json'

class TestSolarCalculator(TestCase):
    """Tests for the Solar Calculator."""

    def setUp(self):
        """Setup Solar Calculator Objects."""

        test = SolarCalculator(
            user_location={"latitude": "47.466748", "longitude": "-122.34722"}, 
            current_date=datetime(2021, 5, 1), 
            water_interval=10, 
            light_type="West")

        test2 = SolarCalculator(
            user_location={"latitude": "45.520247", "longitude": "-122.674195"}, 
            current_date=datetime(2021, 5, 1), 
            water_interval=21, 
            light_type="North")

        self.test1 = test
        self.test2 = test2
    
    def test_create_solar_calculator(self):
        """Test creating a new solar calculator object."""

        self.assertIsInstance(self.test1, SolarCalculator)
        self.assertIsInstance(self.test2, SolarCalculator)

    def test_generate_dates(self):
        """Test generating a list of date objects."""

        list1 = self.test1.generate_dates(self.test1.current_date, self.test1.water_interval)
        list2 = self.test2.generate_dates(self.test2.current_date, self.test2.water_interval)

        self.assertEqual(len(list1), 10)
        self.assertEqual(len(list2), 21)
        self.assertIsInstance(list1[5], datetime)
        self.assertIsInstance(list2[12], datetime)
    
    def test_convert_str_to_datetime(self):
        """Test taking a datetime object and a string and combining both into a datetime object."""

        date1 = datetime(1990, 1, 5)
        date2 = datetime(2021, 4, 21)
        time1 = '13:30:20'
        time2 = '9:55:17'

        conversion1 = self.test1.convert_str_to_datetime(date1, time1)
        conversion2 = self.test2.convert_str_to_datetime(date2, time2)

        self.assertIsInstance(conversion1, datetime)
        self.assertIsInstance(conversion2, datetime)
        self.assertEqual(conversion1, datetime(1990, 1, 5, 13, 30, 20))
        self.assertEqual(conversion2, datetime(2021, 4, 21, 9, 55, 17))
    
    def test_convert_UTC_to_localtime(self):
        """Test converting a UTC date/time into a local date/time.
        
        These tests are configured for local Pacific (PDT or PST) time. Additional
        values are needed to test other local timezones."""

        date1 = date(2010, 11, 19)
        date2 = date(2021, 8, 7)
        time1 = '5:10:09 PM'
        time2 = '6:25:55 AM'

        conversion1 = self.test1.convert_UTC_to_localtime(date1, time1)
        conversion2 = self.test2.convert_UTC_to_localtime(date2, time2)

        self.assertIsInstance(conversion1, datetime)
        self.assertIsInstance(conversion2, datetime)

        self.assertEqual(conversion1.year, 2010)
        self.assertEqual(conversion1.day, 19)
        self.assertEqual(conversion1.month, 11)
        self.assertEqual(conversion2.year, 2021)
        self.assertEqual(conversion2.month, 8)
        self.assertEqual(conversion2.day, 7-1) #accounts for UTC -5 to UTC -11 because morning falls the previous day

        #The following tests assume that the local timezone is Pacific Time. Other timezones will fail these tests. Local timezone is set by the method.

        # 11/19/2010 was in PST time -8 hours behind UTC time 9:10:09 AM
        self.assertEqual(conversion1.hour, 9)
        self.assertEqual(conversion1.minute, 10)
        self.assertEqual(conversion1.second, 9)
        # 8/7/2021 will be in PDT time -7 hours behind UTC time 23:25:55 PM
        self.assertEqual(conversion2.hour, 23)
        self.assertEqual(conversion2.minute, 25)
        self.assertEqual(conversion2.second, 55)
    
    def test_get_data(self):
        """Test getting data from the sunrise/sunset API for a specific day/time."""

        day1 = self.test1.get_data(datetime(2021, 5, 1))
        day2 = self.test2.get_data(datetime(2021, 5, 1))

        self.assertIsNot(day1['sunrise'], None)
        self.assertIsNot(day1['sunset'], None)
        self.assertIsNot(day1['solar_noon'], None)
        self.assertIsNot(day1['day_length'], None)

        self.assertIsInstance(day2['sunrise'], datetime)
        self.assertIsInstance(day2['sunset'], datetime)
        self.assertIsInstance(day2['solar_noon'], datetime)
        self.assertIsInstance(day2['day_length'], datetime)

        # "latitude": "47.466748", "longitude": "-122.34722"
        self.assertEqual(day1['sunrise'].day, 1)
        self.assertEqual(day1['sunrise'].hour, 5)
        self.assertEqual(day1['sunrise'].minute, 50)
        self.assertEqual(day1['sunset'].day, 1)
        self.assertEqual(day1['sunset'].hour, 20)
        self.assertEqual(day1['sunset'].minute, 22)
        self.assertEqual(day1['solar_noon'].day, 1)
        self.assertEqual(day1['solar_noon'].hour, 13)
        self.assertEqual(day1['solar_noon'].minute, 6)
        self.assertEqual(day1['day_length'].day, 1)
        self.assertEqual(day1['day_length'].hour, 14)
        self.assertEqual(day1['day_length'].minute, 31)