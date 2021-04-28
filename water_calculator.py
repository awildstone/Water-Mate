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
            water_interval=self.water_schedule.water_interval
            light_type = self.light_type
            )

        light_forcast = calculator.get_daily_sunlight()

        #I'm going to add some error handling in case the API I am using doesn't return values.
        if (light_forcast):
            return light_forcast
        raise ConnectionRefusedError #not sure if this is the appropriate error I should be raising?

    def calculate_next_water_date(self):
        """Calculates the water_interval and next_water_date using data from the plant type's base_water (days between water frequency), 
        plant type's base_sunlight (optium daily sunlight requirements), and the calculated light forcast.
        
        The plant's water_schedule -> water_interval will adjust based on how how much or how little light a plant is recieving each day compared to the plant type's base_sunlight requirements to thrive. Less light will increase the frequency length between waterings, more sunlight will decrease the frequency length between waterings (water_interval)."""

        #base_water is the number of days between watering for this type of plant under optimal conditions
        base_water = self.plant_type.base_water
        #base_light is the optimal daily amount of sunlight for this type of plant
        base_light = self.plant_type.base_sunlight


        for time in self.light_forcast:
            #convert the timedelta to datetime.time()? add all of the times up and divide by number of days to get average light per day.

            #compare the avg light_forcast with the plant type base_light

            #if the avg light_forcast is higher than the base_light requirement, decrease water interval 1 day or more
            #if the avg light_forcast is lower than the base_light requirement, increase water interval 1 day or more

