"""Solar Calculator & helper methods."""

import requests, json
from datetime import date, datetime, timedelta, timezone
# from dateutil import tz
# import pytz
from tzlocal import get_localzone
from zoneinfo import ZoneInfo

BASE_URL = 'https://api.sunrise-sunset.org/json'
# ALL_TIMEZONES = set(pytz.all_timezones_set)

class SolarCalculator:
    """A class to get the solar forcast calculations based on a user' location,
    the current date, the water_interval (number of days between waterings), and the light type."""

    def __init__(self, user_location, current_date, water_interval, light_type):
        self.user_location = user_location
        self.current_date = current_date
        self.water_interval = water_interval
        self.light_type = light_type

    def generate_dates(self, current_date, water_interval):
        """Generate and return a list of dates starting with the day after the current date
        and ending at the water_interval count."""

        dates = []
        for i in range(1, water_interval + 1):
            date = current_date + timedelta(days=i)
            dates.append(date)

        return dates
    
    def convert_str_to_datetime(self, date, time):
        """Takes a date object and a time string, combines both into a string then returns the datetime object."""

        date_time_str = date.strftime('%Y-%m-%d') + ' ' + time

        return datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
    
    def convert_12_to_24(self, string):
        """Accepts a string, evaluates the string and converts from 12 hour to 24 hour time.
        Solution found here: https://www.geeksforgeeks.org/python-program-convert-time-12-hour-24-hour-format/."""

        #Check if last two elements of time is AM and first two elements are 12
        if string[-2:] == 'AM' and string[:2] == '12':
            return '00' + string[2:-2]
          
        #remove the AM    
        if string[-2:] == 'AM':
            return string[:-3]
      
        #Check if last two elements of time is PM and first two elements are 12   
        if string[-2:] == 'PM' and string[:2] == '12':
            return string[:-3]
          
        else:
            #add 12 to hours and remove PM
            return str(int(string[:2]) + 12) + string[2:8]

    def convert_UTC_to_localtime(self, date, time):
        """Accepts a UTC datetime object and a 12-hour formatted string in UTC time. Converts UTC time to local time then
        returns a newly formatted localtime datetime object.
        Found solution on https://stackoverflow.com/questions/4770297/convert-utc-datetime-string-to-local-datetime 
        and https://howchoo.com/g/ywi5m2vkodk/working-with-datetime-objects-and-timezones-in-python."""

        converted_time = None

        if time[1] == ':':
            length = len(time)
            new_time = time.zfill(length + 1)
            converted_time = self.convert_12_to_24(new_time)
        else:
            converted_time = self.convert_12_to_24(time)

        from_zone = ZoneInfo('UTC')
        to_zone = get_localzone()

        #build a utc formatted string from API response string
        utc_date_time_str = date.strftime('%Y-%m-%d') + ' ' + converted_time
        #parse string into datetime obj
        utc_date_time = datetime.strptime(utc_date_time_str, '%Y-%m-%d %H:%M:%S')
        #set datetime obj timezone to UTC
        utc_date_time = utc_date_time.replace(tzinfo=from_zone)
        #convert the datetime UTC object to local date/time
        local_date_time = utc_date_time.astimezone(to_zone)

        return local_date_time

    def get_data(self, day):
        """Calls the Sunset and sunrise times API for a given date with the user_location.
        Returns the JSON data in dict for this date/location.
        {"date": date, "sunrise": sunrise, "sunset": sunset, "day_length": day_length, "solar_noon": solar_noon}.
        
        Currently, this only supports conversions from UTC to timezones between UTC -5 to UTC -11."""

        response = requests.get(BASE_URL, params={
            'lat': self.user_location['latitude'], 
            'lng': self.user_location['longitude'], 
            'date': day})
        
        results = response.json()['results']

        # print('################### LOCAL DATE ###################')
        # print(day)
        # print('################### SUNRISE ###################')
        # print(results['sunrise'])
        # print('################### SUNSET ###################')
        # print(results['sunset'])
        # print('################### SOLAR NOON ###################')
        # print(results['solar_noon'])
        # print('################### DAY LENGTH ###################')
        # print(results['day_length'])

        if response.json()['status'] == 'OK':
            return {'date': day, 
            'sunrise': self.convert_UTC_to_localtime(day, results['sunrise']), 
            'sunset': self.convert_UTC_to_localtime(day + timedelta(days=1), results['sunset']), #adding 1 day to account that the morning in UTC time falls in the evening of the previous day in Pacific Time (PST/PDT). I have some work to do to support different timezones but for now this works for timezones between UTC -5 to UTC -11.
            'solar_noon': self.convert_UTC_to_localtime(day, results['solar_noon']), #add 12 hours to convert results from 12 hour time to 24 hour time.
            'day_length': self.convert_str_to_datetime(day, results['day_length'])}

    def get_solar_schedule(self):
        """Generates and returns a list of data for given number of dates:
        [{"date": date, "sunrise": sunrise, "sunset": sunset, "day_length": day_length}, etc.]"""

        solar_schedule = []
        dates = self.generate_dates(self.current_date, self.water_interval)

        for day in dates:
            data = self.get_data(day)
            solar_schedule.append(data)
        
        return solar_schedule
    
    # Calculation to convert point in time to duration found on https://stackoverflow.com/questions/35241643/convert-datetime-time-into-datetime-timedelta-in-python-3-4
    def get_fraction_of_time(self, time, fraction):
        """ Accepts time (total daily hours), and a fraction that represents the fraction of total time we need. 
        Converts time into a duration of time then gets the fraction of that time.

        Returns the fraction of the duration of time."""

        duration_of_time = datetime.combine(date.min, time) - datetime.min
        fraction_of_total_time = duration_of_time * fraction

        return fraction_of_total_time

    def get_daily_sunlight(self):
        """Calculates the maximum amount of light that a light_type can recieve given the user location, the date, and the type of light source. Uses data from the solar forecast to calculate the maximum sunlight potential for each day.
        Returns a list of time deltas that equal the maximum potential sunlight for each day."""

        solar_forcast = self.get_solar_schedule()
        
        solar_noon_times = [date['solar_noon'] for date in solar_forcast]
        sunrise_times = [date['sunrise'] for date in solar_forcast]
        sunset_times = [date['sunset'] for date in solar_forcast]
        day_lengths = [date['day_length'] for date in solar_forcast]

        plant_max_daily_light = []

        for i in range(len(solar_forcast)):
            nh_light_calculations = {
                "North": self.get_fraction_of_time(day_lengths[i].time(), .0625), #none to little sunlight - 1/16 of total daylight
                "East": sunrise_times[i] - solar_noon_times[i], #sunrise-midday (soft morning light)
                "South": self.get_fraction_of_time(day_lengths[i].time(), 0.875), #sunrise to sunset - 7/8 of total daylight
                "West": solar_noon_times[i] - sunset_times[i], #midday-sunset (hard afternoon light)
                "Northeast": self.get_fraction_of_time(day_lengths[i].time(), .125), # 1/8 of daily sun (soft morning light)
                "Northwest": self.get_fraction_of_time(day_lengths[i].time(), .125), # 1/8 of daily sun (hard afternoon light)
                "Southeast": self.get_fraction_of_time(day_lengths[i].time(), .75), #sunrise-midday (soft morning light) - 3/4 of total daylight
                "Southwest": self.get_fraction_of_time(day_lengths[i].time(), .75), #midday-sunset (hard afternoon light) - 3/4 of total daylight
            }

            sh_light_calculations = {
                "North": self.get_fraction_of_time(day_lengths[i].time(), 0.875), #sunrise to sunset - 7/8 of total daylight
                "East": sunrise_times[i] - solar_noon_times[i], #sunrise-midday (soft morning light)
                "South": self.get_fraction_of_time(day_lengths[i].time(), .0625), #none to little sunlight - 1/16 of total daylight
                "West": solar_noon_times[i] - sunset_times[i], #midday-sunset (hard afternoon light)
                "Northeast": self.get_fraction_of_time(day_lengths[i].time(), .75), #sunrise-midday (soft morning light) - 3/4 of total daylight
                "Northwest": self.get_fraction_of_time(day_lengths[i].time(), .75), #midday-sunset (hard afternoon light) - 3/4 of total daylight
                "Southeast": self.get_fraction_of_time(day_lengths[i].time(), .125), # 1/8 of daily sun (soft morning light) 
                "Southwest": self.get_fraction_of_time(day_lengths[i].time(), .125), # 1/8 of daily sun (hard afternoon light)
            }

            if float(self.user_location['latitude']) > 0:
                #user is in the northern hemisphere
                # print(nh_light_calculations[self.light_type])
                plant_max_daily_light.append(nh_light_calculations[self.light_type])
            else:
                #user is in the southern hemisphere
                # print(sh_light_calculations[self.light_type])
                plant_max_daily_light.append(sh_light_calculations[self.light_type])
            
        return plant_max_daily_light

