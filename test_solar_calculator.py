"""Solar Calculator Tests."""

#FLASK_ENV=production python3 -m unittest test_solar_calculator.py

from unittest import TestCase
from datetime import date, datetime, timedelta, timezone
from tzlocal import get_localzone
from solar_calculator import SolarCalculator

BASE_URL = 'https://api.sunrise-sunset.org/json'

class TestSolarCalculator(TestCase):
    """Tests for the Solar Calculator."""

    def setUp(self):
        """Setup Solar Calculator Objects."""

        test1 = SolarCalculator(
            user_location={"latitude": "47.466748", "longitude": "-122.34722"}, 
            current_date=datetime(2021, 5, 1), 
            water_interval=10, 
            light_type="West")

        test2 = SolarCalculator(
            user_location={"latitude": "45.520247", "longitude": "-122.674195"}, 
            current_date=datetime(2021, 5, 1), 
            water_interval=21, 
            light_type="North")
        
        test3 = SolarCalculator(
            user_location={"latitude": "45.520247", "longitude": "-122.674195"}, 
            current_date=datetime(2021, 5, 1), 
            water_interval=7, 
            light_type="East")

        self.test1 = test1
        self.test2 = test2
        self.test3 = test3
    
    def test_create_solar_calculator(self):
        """Test creating a new solar calculator object."""

        self.assertIsInstance(self.test1, SolarCalculator)
        self.assertIsInstance(self.test2, SolarCalculator)

    def test_generate_dates(self):
        """Test generating a list of date objects."""

        list1 = self.test1.generate_dates()
        list2 = self.test2.generate_dates()

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
    
    def test_convert_12_to_24(self):
        """Test converting a 12-hour format string time into a 24-hour format string time."""

        time1 = '01:09:55 PM'
        time2 = '03:17:20 PM'
        time3 = '12:40:01 PM'
        time4 = '10:30:45 AM'
        time5 = '12:00:59 AM'

        self.assertEqual(self.test1.convert_12_to_24(time1), '13:09:55')
        self.assertEqual(self.test1.convert_12_to_24(time2), '15:17:20')
        self.assertEqual(self.test1.convert_12_to_24(time3), '12:40:01')
        self.assertEqual(self.test1.convert_12_to_24(time4), '10:30:45')
        self.assertEqual(self.test1.convert_12_to_24(time5), '00:00:59')
    
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
        self.assertEqual(conversion2.day, 7-1) #accounts for UTC -5 to UTC -11 because morning of UTC falls the previous day in local timezone

        #The following tests assume that the local timezone is Pacific Time. Other timezones will fail these tests. Local timezone is set by the convert_UTC_to_localtime() method.

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

    def test_get_solar_schedule(self):
        """Test calculating and building the solar schedule a list containting:
        {"date": date, "sunrise": sunrise, "sunset": sunset, "day_length": day_length, "solar_noon": solar_noon}
        for the number of days in the Solar Calculator Water interval."""

        solar_schedule1 = self.test1.get_solar_schedule()
        solar_schedule2 = self.test2.get_solar_schedule()

        self.assertEqual(len(solar_schedule1), 10)
        self.assertEqual(solar_schedule1[0]['date'], datetime(2021, 5, 2))
        self.assertEqual(solar_schedule1[9]['date'], datetime(2021, 5, 11))

        self.assertEqual(len(solar_schedule2), 21)
        self.assertEqual(solar_schedule2[0]['date'], datetime(2021, 5, 2))
        self.assertEqual(solar_schedule2[20]['date'], datetime(2021, 5, 22))
    
    def test_get_fraction_of_time(self): 
        """Take a timedelta and a fraction and return a timedelta that is a fraction of that time."""

        solar_schedule1 = self.test1.get_solar_schedule()
        solar_schedule2 = self.test2.get_solar_schedule()

        day_length1 = solar_schedule1[0]['day_length'].time() # 14:34:31
        day_length2 = solar_schedule1[1]['day_length'].time() # 14:37:26
        day_length3 = solar_schedule1[2]['day_length'].time() # 14:40:19
        day_length4 = solar_schedule2[0]['day_length'].time() # 14:24:19
        day_length5 = solar_schedule2[1]['day_length'].time() # 14:27:02
        day_length6 = solar_schedule2[2]['day_length'].time() # 14:29:42

        fraction1 = 0.0625 # 1/16
        fraction2 = 0.125 # 1/8
        fraction3 = 0.75 # 3/4
        fraction4 = 0.875 # 7/8
        fraction5 = 0.50 # 1/2
        #use http://www.csgnetwork.com/fracttimeconv.html to check math

        # 14.575277777777778 * 0.875 = 12.7533 = 12:45:10
        #12:45:12.125000 = timedelta(seconds=45912, microseconds=125000)
        self.assertEqual(self.test1.get_fraction_of_time(day_length1, fraction4), timedelta(seconds=45912, microseconds=125000))

        # 14.623888888888889 * 0.0625 = 0.9139 = 0:54:50
        #0:54:50.375000 = timedelta(seconds=3290, microseconds=375000)
        self.assertEqual(self.test1.get_fraction_of_time(day_length2, fraction1), timedelta(seconds=3290, microseconds=375000))

        # 14.671944444444444 * 0.125 = 1.8339 = 1:50:02
        # 1:50:02.375000 = timedelta(seconds=6602, microseconds=375000)
        self.assertEqual(self.test1.get_fraction_of_time(day_length3, fraction2), timedelta(seconds=6602, microseconds=375000))

        # 14.405277777777778 * 0.75 = 10.8039 = 10:48:10
        # 10:48:14.250000 = timedelta(seconds=38894, microseconds=250000)
        self.assertEqual(self.test2.get_fraction_of_time(day_length4, fraction3), timedelta(seconds=38894, microseconds=250000))
    
        # 14.450555555555555 * 0.5 = 7.2252 = 7:13:30
        # 7:13:31 = timedelta(seconds=26011, microseconds=0)
        self.assertEqual(self.test2.get_fraction_of_time(day_length5, fraction5), timedelta(seconds=26011, microseconds=0))

        # 14.495 * 0.75 = 10.8712 = 10:52:15
        # 10:52:16.500000 = timedelta(seconds=39136, microseconds=500000)
        self.assertEqual(self.test2.get_fraction_of_time(day_length6, fraction3), timedelta(seconds=39136, microseconds=500000))

    def test_get_daily_sunlight(self):
        """This is the main function of this class that uses all of the other functions to calculate the max daily
        total hours a plant recieves given the user location, current date (the water date), water interval (how many days
        until the next water), and light type. Calculates a timedelta list for the max hours for each day."""


        daily_sunlight1 = self.test1.get_daily_sunlight()
        daily_sunlight3 = self.test3.get_daily_sunlight()

        self.assertEqual(len(daily_sunlight1), 10)
        self.assertEqual(len(daily_sunlight3), 7)

        # solar_schedule1 = self.test1.get_solar_schedule()
        # print('Solar Noon: ', solar_schedule1[0]['solar_noon'].time())
        # print('Sunset: ', solar_schedule1[0]['sunset'].time())
        # light type is West. Calculation is (solar_noon_times[i] - sunset_times[i]) = timedelta
        # (solar_noon = 13:06:15) - (sunset = 20:23:31)  ~ 7:17:16
        self.assertEqual(daily_sunlight1[0], timedelta(seconds=26236))

        # for day in daily_sunlight1:
        #     print(day)

        # solar_schedule3 = self.test3.get_solar_schedule()
        # print('Sunrise: ', solar_schedule3[0]['sunrise'].time())
        # print('Solar Noon: ', solar_schedule3[0]['solar_noon'].time())
        #light type is East. Calculation is sunrise_times[i] - solar_noon_times[i] = timedelta
        # (sunrise = 05:55:24) - (solar_noon = 13:07:34) = 7:12:10
        self.assertEqual(daily_sunlight3[0], timedelta(seconds=25930))

        # for day in daily_sunlight3:
        #     print(day)