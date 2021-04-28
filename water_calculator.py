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
        """Get the light forcast from the solar calculator."""

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
        plant type's base_sunlight (optium daily sunlight requirements), and the user location solar schedule.
        
        In addition, we will look at the plant's light source and user latitude to calculate the maximum
        light potential the plant can recieve. Users in the northern hemisphere will have positive latitudes and users in the southern
        hemisphere will use negative latitudes.
        
        The plant -> water_schedule -> water_interval will adjust based on how how much or how little light a plant is recieving each day compared to the plant type's -> base_sunlight requirements to thrive. Less sunlight will increase the frequency length between waterings, more sunlight will decrease the frequency length between waterings (water_interval)."""

