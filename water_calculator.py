"""Water Calculator & helper methods."""

from solar_calculator import SolarCalculator
from datetime import datetime

class WaterCalculator:
    """A class to make water schedule calculations.
    Takes a User, a plant type, and a water_schedule."""

    def __init__(self, user, plant_type, water_schedule, light_type):
        self.user = user
        self.plant_type = plant_type
        self.water_schedule = water_schedule
        self.light_type = light_type
        self.light_forcast = self.get_light_forcast()
    
    def get_light_forcast(self):
        """Get the light forcast from the solar calculator.
        Uses the user's location, current date, water interval (days between water frequency),
        and the light type to calculate the maximum light potential for each day.
        
        If the light forcast fails to populate raise an error."""

        calculator = SolarCalculator(
            user_location=self.user.get_coordinates,
            current_date=self.water_schedule.water_date,
            water_interval=self.water_schedule.water_interval,
            light_type = self.light_type
            )

        light_forcast = calculator.get_daily_sunlight()

        if (light_forcast):
            return light_forcast
        raise ConnectionRefusedError #not sure if this is the appropriate error I should be raising?
    
    def convert_timedelta_to_float(self, time_delta):
        """Accepts a datetime.timedelta object, extracts the minutes and microseconds,
        then converts the total minutes and microseconds to hours.
        Returns a float representing the total hours."""

        seconds = time_delta.seconds
        microseconds = time_delta.microseconds

        return (microseconds / 1000000 + seconds / 60) / 60
    
    def calculate_average_hours(self, time_list):
        """Accepts a list of datetime.timedelta objects, calculates and returns the average."""
        
        total = 0
        for time in time_list:
            hours = self.convert_timedelta_to_float(time)
            total = total + hours
        
        return total / len(time_list)


    def calculate_water_interval(self):
        """Calculates the water_interval and next_water_date using data from the plant type's base_water (days between water frequency), 
        plant type's base_sunlight (optium daily sunlight requirements), and the calculated light forcast.
        
        The plant's water_schedule -> water_interval will adjust based on how how much or how little light a plant is recieving each day compared to the plant type's base_sunlight requirements to thrive (average_hours - base_light). Negative difference means the plant needs more light for optimal conditions so the frequency length between waterings should increase (less frequent watering). Positive difference means the plant is getting above optimal light conditions so the frequency between waterings should decrease (more frequent watering).
        
        Other considerations in this algorithm:
        1. Sometimes a home cannot provide ideal light conditions for the plant's type no matter what and the watering algorithm could continue to adjust the schedule due to poor conditions. Therefore, a max days-without-water threshold will be set by the algorithm with the max_days_without_water coming from the plant type.

        2. Sometimes the algorithm may attempt to make a correction or extreme correction that may set the water_interval to a negative number. In this case the algorithm will "reset" the water_interval to 3 days and then the user can check the plant's condition and water or snooze accordingly.

        3. The algorithm threshold looks at the average light the plant recieves in the water interval period compared to the optimal light conditions for that plant type and makes minor water adjustments for minor differences, and more extreme adjustments for larger differences in an attempt to correct the water schedule.

        4. No matter what, the water_interval will never exceed the plant type max_days_without_water so plants in less than optimal conditions will recieve enough water to stay alive and plants in extreme conditions will not recieve too much water so as to cause root rot."""

        # base_water = self.plant_type.base_water
        base_light = self.plant_type.base_sunlight
        new_water_interval = self.water_schedule.water_interval

        #compare the average hours with the optimal hours and adjust accordingly given the respective thresholds
        average_hours = self.calculate_average_hours(self.light_forcast)
        
        res = average_hours - base_light
        adjustment = 0
        
        positive_threshold = {
            res >= 0 and res < 1: 0,
            res >= 1 and res < 3: -1, 
            res >= 3 and res < 6: -2,
            res >= 6 and res < 9: -7,
            res >= 10: -20}

        negative_threshold = {
            res <= 0 and res > -1: 0,
            res <= -1 and res > -3: 1, 
            res <= -3 and res > -6: 2,
            res <= -6 and res > -9: 7,
            res <= -10: 20}
        
        if res >= 0:
            #the plant is getting too much light
            for key in positive_threshold:
                if (key):
                    adjustment = positive_threshold[key]
        else:
            #the plant is not getting enough light
            for key in negative_threshold:
                if (key):
                    adjustment = negative_threshold[key]
        
        #set the new number of days between watering
        new_water_interval += adjustment

        #last, make sure the water_interval does not exceed the plant type's max_days_without_water or go into negative.
        if new_water_interval >= self.plant_type.max_days_without_water:
            new_water_interval = self.plant_type.max_days_without_water
        
        if new_water_interval <= 0:
            new_water_interval = 3
        
        return new_water_interval      
