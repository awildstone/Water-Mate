"""Water Calculator & helper methods."""

class WaterCalculator:
    """A class to make water schedule calculations.
    Takes a User, a plant, and a water_schedule."""

     def __init__(self, user, plant, water_schedule, solar_forcast):
        self.user = user
        self.plant = plant
        self.water_schedule = water_schedule
        self.solar_forcast = solar_forcast
