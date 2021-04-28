"""Solar Calculator & helper methods."""

import requests, json
from datetime import date, datetime, timedelta, timezone

BASE_URL = 'https://api.sunrise-sunset.org/json'

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

    def convert_UTC__to_localtime(self, date, time):
        """Builds a UTC datetime object then converts UTC time to local time. 
        Returns localtime datetime object."""

        #build a utc formatted string from API response string
        utc_date_time_str = date.strftime('%Y-%m-%d') + ' ' + time[:-3]
        #convert the string to a UTC datetime object
        utc_date_time_obj = datetime.strptime(utc_date_time_str, '%Y-%m-%d %H:%M:%S')

        return utc_date_time_obj.replace(tzinfo=timezone.utc).astimezone(tz=None)

    def get_data(self, day):
        """Calls the Sunset and sunrise times API for a given date with the user_location.
        Returns the JSON data in dict for this date/location.
        {"date": date, "sunrise": sunrise, "sunset": sunset, "day_length": day_length, "solar_noon": solar_noon}."""

        response = requests.get(BASE_URL, params={
            'lat': self.user_location['latitude'], 
            'lng': self.user_location['longitude'], 
            'date': day})
        
        results = response.json()['results']
        
        return {'date': day, 
        'sunrise': self.convert_UTC__to_localtime(day, results['sunrise']), 
        'sunset': self.convert_UTC__to_localtime(day, results['sunset']), 
        'solar_noon': self.convert_UTC__to_localtime(day, results['solar_noon']),
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

        Returns the fraction of the duration of time.
        
        This calculation is used to calculate the total amount of light in Northeastern/NorthWestern (Northern Hemisphere) exposure or Southeastern/Southwestern (Southern Hemisphere) exposure."""

        duration_of_time = datetime.combine(date.min, time) - datetime.min
        fraction_of__total_time = duration_of_time * fraction

        return fraction_of__total_time

    # Calculation to convert point in time to duration found on https://stackoverflow.com/questions/35241643/convert-datetime-time-into-datetime-timedelta-in-python-3-4
    def get_datetime_fraction(self, time, fraction):
        """ Accepts time (total daily hours), and a fraction that represents the fraction of time we need to subtract from the total daily hours. 
        Converts the time into a duration of time then gets the fraction of that time.
        Returns the total time - fraction of time.
        
        This calculation is used to calculate the total amount of light in a Southern (Northern Hemisphere) exposure or Northern (Southern Hemisphere) exposure."""

        duration_of_time = datetime.combine(date.min, time) - datetime.min
        fraction_of__total_time_removed = duration_of_time - (duration_of_time * fraction)

        return fraction_of__total_time_removed

    def get_daily_sunlight(self):
        """Calculates the maximum amount of light that a light_type can recieve given the user location, the date, and the type of light source. Uses data from the solar forecast to calculate the maximum sunlight potential for each day.
        Returns a list of time deltas that equal the maximum potential sunlight for each day."""

        solar_forcast = self.get_solar_schedule()
        # print(solar_forcast)
        
        solar_noon_times = [date['solar_noon'] for date in solar_forcast]
        sunrise_times = [date['sunrise'] for date in solar_forcast]
        sunset_times = [date['sunset'] for date in solar_forcast]
        day_lengths = [date['day_length'] for date in solar_forcast]

        plant_max_daily_light = []

        for i in range(len(solar_forcast)):
            nh_light_calculations = {
                "North": self.get_fraction_of_time(day_lengths[i].time(), .0625), #none to little sunlight - 1/16 of total daylight
                "East": sunrise_times[i] - solar_noon_times[i], #sunrise-midday (soft morning light)
                "South": self.get_datetime_fraction(day_lengths[i].time(), .25), #sunrise to sunset - 1/4 of total time
                "West": solar_noon_times[i] - sunset_times[i], #midday-sunset (hard afternoon light)
                "Northeast": self.get_fraction_of_time(day_lengths[i].time(), .125), # 1/8 of daily sun (soft morning light)
                "Northwest": self.get_fraction_of_time(day_lengths[i].time(), .125), # 1/8 of daily sun (hard afternoon light)
                "Southeast": sunrise_times[i] - solar_noon_times[i], #sunrise-midday (soft morning light)
                "Southwest": solar_noon_times[i] - sunset_times[i], #midday-sunset (hard afternoon light)
            }

            sh_light_calculations = {
                "North": self.get_datetime_fraction(day_lengths[i].time(), .25), #sunrise to sunset - 1/4 of total time
                "East": sunrise_times[i] - solar_noon_times[i], #sunrise-midday (soft morning light)
                "South": self.get_fraction_of_time(day_lengths[i].time(), .0625), #none to little sunlight - 1/16 of total daylight
                "West": solar_noon_times[i] - sunset_times[i], #midday-sunset (hard afternoon light)
                "Northeast": sunrise_times[i] - solar_noon_times[i], #sunrise-midday (soft morning light)
                "Northwest": solar_noon_times[i] - sunset_times[i], #midday-sunset (hard afternoon light)
                "Southeast": self.get_fraction_of_time(day_lengths[i].time(), .125), # 1/8 of daily sun (soft morning light) 
                "Southwest": self.get_fraction_of_time(day_lengths[i].time(), .125), # 1/8 of daily sun (hard afternoon light)
            }

            if float(self.user_location['latitude']) > 0:
                #user is in the northern hemisphere
                print(nh_light_calculations[self.light_type])
                plant_max_daily_light.append(nh_light_calculations[self.light_type])
            else:
                #user is in the southern hemisphere
                print(sh_light_calculations[self.light_type])
                plant_max_daily_light.append(sh_light_calculations[self.light_type])
            
        return plant_max_daily_light

test = SolarCalculator(user_location={"latitude": "47.466748", "longitude": "-122.34722"}, current_date=datetime.today(), water_interval=7, light_type="South")

test2 = SolarCalculator(user_location={"latitude": "-33.854816", "longitude": "151.216454"}, current_date=datetime.today(), water_interval=7, light_type="South")

light_forcast = test.get_daily_sunlight()

print('################# LIGHT FORCAST BURIEN WA #################')
print(light_forcast)


# light_forcast2 = test2.get_daily_sunlight()
# print('################# LIGHT FORCAST SYDNEY AUSTRALIA #################')
# print(light_forcast2)
