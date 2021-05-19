"""Solar Calculator & helper methods."""

import requests, json
from datetime import date, datetime, timedelta

BASE_URL = 'https://api.sunrise-sunset.org/json'

class SolarCalculator:
    """A class to get the solar forcast calculations based on a user' location,
    the current date, the water_interval (number of days between waterings), and the light type."""

    def __init__(self, user_location, current_date, water_interval, light_type):
        self.user_location = user_location
        self.current_date = current_date
        self.water_interval = water_interval
        self.light_type = light_type

    def generate_dates(self):
        """Generate and return a list of dates starting with the day after the current date
        and ending at the water_interval count."""

        dates = []
        for i in range(1, self.water_interval + 1):
            date = self.current_date + timedelta(days=i)
            dates.append(date)

        return dates
    
    def convert_str_to_datetime(self, date, time):
        """Takes a date object and a time string, combines both into a string then returns the datetime object."""

        converted_time = None
        if time[-2:] != 'AM' and time[-2:] != 'PM': #added this condition to account for total_daylight case which does not have AM/PM.
            converted_time = time
        elif time[1] == ':':
            length = len(time)
            new_time = time.zfill(length + 1)
            converted_time = self.convert_12_to_24(new_time)
        else:
            converted_time = self.convert_12_to_24(time)

        date_time_str = date.strftime('%Y-%m-%d') + ' ' + converted_time

        return datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S')
    
    def convert_12_to_24(self, string):
        """Accepts a string, evaluates the string and converts from 12 hour to 24 hour time.
        Solution found here: https://www.geeksforgeeks.org/python-program-convert-time-12-hour-24-hour-format/."""

        #Check if last two elements of time is AM and first two elements are 12
        if string[-2:] == 'AM' and string[:2] == '12':
            return '00' + string[2:-3]
        #remove the AM    
        if string[-2:] == 'AM':
            return string[:-3]
        #Check if last two elements of time is PM and first two elements are 12   
        if string[-2:] == 'PM' and string[:2] == '12':
            return string[:-3]
        #add 12 to hours and remove PM
        return str(int(string[:2]) + 12) + string[2:8]

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

        if response.json()['status'] == 'OK':
            return {'date': day, 
            'sunrise': self.convert_str_to_datetime(day, results['sunrise']),
            # adding 1 day to account that the morning in UTC time falls in the evening of the previous day in Pacific Time (PST/PDT). 
            # I have some work to do to support different timezones but for now this works for timezones between UTC -5 to UTC -11.
            'sunset': self.convert_str_to_datetime(day + timedelta(days=1), results['sunset']),
            'solar_noon': self.convert_str_to_datetime(day, results['solar_noon']),
            'day_length': self.convert_str_to_datetime(day, results['day_length'])}

    def get_solar_schedule(self):
        """Generates and returns a list of data for given number of dates:
        [{"date": date, "sunrise": sunrise, "sunset": sunset, "day_length": day_length, "solar_noon": solar_noon}, {etc.]"""

        solar_schedule = []
        dates = self.generate_dates()

        for day in dates:
            data = self.get_data(day)
            solar_schedule.append(data)
        
        return solar_schedule
    
    def get_fraction_of_time(self, time, fraction):
        """ Accepts time (total daily hours), and a fraction that represents the fraction of total time we need. 
        Converts time into a duration of time then gets the fraction of that time.

        Returns the fraction of the duration of time.
        
        Calculation to convert point in time to duration found on https://stackoverflow.com/questions/35241643/convert-datetime-time-into-datetime-timedelta-in-python-3-4"""

        duration_of_time = datetime.combine(date.min, time) - datetime.min
        fraction_of_total_time = duration_of_time * fraction

        return fraction_of_total_time

    def get_daily_sunlight(self):
        """Calculates the maximum amount of light that a light_type can recieve given the user location, the date, and the type of light source. Uses data from the solar forecast to calculate the maximum sunlight potential for each day.

        For calculating East and West lightsource types subtracting the later time from the first time difference = later_time - first_time creates a datetime object that only holds the difference.
        
        Returns a list of time deltas that equal the maximum potential sunlight for each day."""

        solar_forcast = self.get_solar_schedule()
        
        solar_noon_times = [date['solar_noon'] for date in solar_forcast]
        sunrise_times = [date['sunrise'] for date in solar_forcast]
        sunset_times = [date['sunset'] for date in solar_forcast]
        day_lengths = [date['day_length'] for date in solar_forcast]

        plant_max_daily_light = []

        #put this in its own method, pull out the decimals as constants
        #create a contstants.py file

        for i in range(len(solar_forcast)):
            nh_light_calculations = {
                "North": self.get_fraction_of_time(day_lengths[i].time(), .0625), #none to little sunlight - 1/16 of total daylight
                "East": solar_noon_times[i] - sunrise_times[i], #sunrise-midday (soft morning light)
                "South": self.get_fraction_of_time(day_lengths[i].time(), 0.875), #sunrise to sunset - 7/8 of total daylight
                "West": sunset_times[i] - solar_noon_times[i], #midday-sunset (hard afternoon light)
                "Northeast": self.get_fraction_of_time(day_lengths[i].time(), .125), # 1/8 of daily sun (soft morning light)
                "Northwest": self.get_fraction_of_time(day_lengths[i].time(), .125), # 1/8 of daily sun (hard afternoon light)
                "Southeast": self.get_fraction_of_time(day_lengths[i].time(), .75), #sunrise-midday (soft morning light) - 3/4 of total daylight
                "Southwest": self.get_fraction_of_time(day_lengths[i].time(), .75), #midday-sunset (hard afternoon light) - 3/4 of total daylight
            }

            sh_light_calculations = {
                "North": self.get_fraction_of_time(day_lengths[i].time(), 0.875), #sunrise to sunset - 7/8 of total daylight
                "East": solar_noon_times[i] - sunrise_times[i], #sunrise-midday (soft morning light)
                "South": self.get_fraction_of_time(day_lengths[i].time(), .0625), #none to little sunlight - 1/16 of total daylight
                "West": sunset_times[i] - solar_noon_times[i], #midday-sunset (hard afternoon light)
                "Northeast": self.get_fraction_of_time(day_lengths[i].time(), .75), #sunrise-midday (soft morning light) - 3/4 of total daylight
                "Northwest": self.get_fraction_of_time(day_lengths[i].time(), .75), #midday-sunset (hard afternoon light) - 3/4 of total daylight
                "Southeast": self.get_fraction_of_time(day_lengths[i].time(), .125), # 1/8 of daily sun (soft morning light) 
                "Southwest": self.get_fraction_of_time(day_lengths[i].time(), .125), # 1/8 of daily sun (hard afternoon light)
            }

            if float(self.user_location['latitude']) > 0:
                #user is in the northern hemisphere
                plant_max_daily_light.append(nh_light_calculations[self.light_type])
            else:
                #user is in the southern hemisphere
                plant_max_daily_light.append(sh_light_calculations[self.light_type])
            
        return plant_max_daily_light