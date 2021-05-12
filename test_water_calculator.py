"""Test Class for Water Calculator."""

# FLASK_ENV=production python3 -m unittest test_water_calculator.py

from unittest import TestCase
from solar_calculator import SolarCalculator
from datetime import datetime, timedelta
from water_calculator import WaterCalculator
from models import User, PlantType, WaterSchedule, LightType

class TestWaterCalculator(TestCase):
    """Tests for the Water Calculator."""

    def setUp(self):
        """Setup new Water Calculator Objects."""

        user = User(
            id=1,
            name='Fake User',
            email='faker@mail.com',
            latitude=47.466748,
            longitude=-122.34722,
            username='fakeuser',
            password='password')
        
        plant_type1 = PlantType(
            id=1,
            name='Cactus',
            base_water=21,
            base_sunlight=14,
            max_days_without_water=90
        )

        plant_type2 = PlantType(
            id=2,
            name='Begonia',
            base_water=7,
            base_sunlight=4,
            max_days_without_water=10
        )

        schedule1 = WaterSchedule(
            id=1,
            water_date=datetime(2021, 4, 13),
            next_water_date=datetime(2021, 5, 1),
            water_interval=10,
            manual_mode=False,
            plant_id=1
        )

        schedule2 = WaterSchedule(
            id=2,
            water_date=datetime(2021, 4, 26),
            next_water_date=datetime(2021, 5, 1),
            water_interval=5,
            manual_mode=False,
            plant_id=2
        )

        light_type1 = LightType(
            id=1,
            type='South'
        )

        light_type2 = LightType(
            id=2,
            type='East'
        )

        wc1 = WaterCalculator(user=user, plant_type=plant_type1, water_schedule=schedule1, light_type=light_type1.type)
        wc2 = WaterCalculator(user=user, plant_type=plant_type2, water_schedule=schedule2, light_type=light_type2.type)

        self.wc1 = wc1
        self.wc2 = wc2
    
    def test_create_water_calculator(self):
        """Test creating a new Water Calculator."""

        self.assertIsInstance(self.wc1, WaterCalculator)
        self.assertIsInstance(self.wc2, WaterCalculator)
        self.assertIsNotNone(self.wc1)
        self.assertIsNotNone(self.wc2)
    
    def test_get_light_forcast(self):
        """Get the light forcast from the Solar Calculator for this Water Calculator."""

        light_forcast1 = self.wc1.get_light_forcast()
        light_forcast2 = self.wc2.get_light_forcast()

        self.assertIsNotNone(light_forcast1)
        self.assertIsNotNone(light_forcast2)

        self.assertEqual(len(light_forcast1), 10)
        self.assertEqual(len(light_forcast2), 5)

        self.assertIsInstance(light_forcast1[0], timedelta)
        self.assertIsInstance(light_forcast1[7], timedelta)
        self.assertIsInstance(light_forcast1[9], timedelta)
        self.assertIsInstance(light_forcast2[0], timedelta)
        self.assertIsInstance(light_forcast2[2], timedelta)
        self.assertIsInstance(light_forcast2[4], timedelta)

    def test_convert_timedelta_to_float(self):
        """Test converting a datetime.timedelta object into a float."""
        
        light_forcast1 = self.wc1.get_light_forcast()
        light_forcast2 = self.wc2.get_light_forcast()

        time1 = light_forcast1[0] # 11:55:48.500000 = 42948 seconds and 500000 microseconds
        time2 = light_forcast1[5] # 12:10:03.375000 = 43803 seconds and 375000 microseconds
        time3 = light_forcast2[0] # 7:09:45 = 25785 seconds and 0 micoseconds
        time4 = light_forcast2[3] # 7:14:17 = 26057 seconds and 0 micoseconds

        float1 = self.wc1.convert_timedelta_to_float(time1)
        float2 = self.wc1.convert_timedelta_to_float(time2)
        float3 = self.wc2.convert_timedelta_to_float(time3)
        float4 = self.wc2.convert_timedelta_to_float(time4)

        # (500000 / 1000000 + 42948 / 60) / 60 = 11.938333333333333
        self.assertEqual(float1, 11.938333333333333)
        
        # (375000 / 1000000 + 43803 / 60) / 60 = 12.17375
        self.assertEqual(float2, 12.17375)

        # (0 / 1000000 + 25785 / 60) / 60 = 7.1625
        self.assertEqual(float3, 7.1625)

        # (0 / 1000000 + 26057 / 60) / 60 = 7.238055555555556
        self.assertEqual(float4, 7.238055555555556)

    def test_calculate_average_hours(self):
        """Test calculatimg the average hours from a list of max daylight forcast. The list of max daylight is
        a list of floats representing the max hours of daylight."""

        light_forcast1 = self.wc1.get_light_forcast()

        #LIGHT FORCAST 1 CONVERTED TO FLOATS
        temp_ls1 = []
        for time in light_forcast1:
            flt = self.wc1.convert_timedelta_to_float(time)
            temp_ls1.append(flt)
        
        #[11.938333333333333, 11.990555555555554, 12.03, 12.087638888888888, 12.130694444444446, 12.17375, 12.220416666666667, 12.267083333333334, 12.31736111111111, 12.367638888888887]

        average1 = self.wc1.calculate_average_hours(light_forcast1)
        # (11.938333333333333 + 11.990555555555554 + 12.03 + 12.087638888888888 + 12.130694444444446 + 12.17375 + 12.220416666666667 + 12.267083333333334 + 12.31736111111111 + 12.367638888888887) / 10 = 12.152347222222222

        self.assertEqual(average1, 12.152347222222222)
        self.assertIsInstance(average1, float)

        light_forcast2 = self.wc2.get_light_forcast()

        #LIGHT FORCAST 1 CONVERTED TO FLOATS
        temp_ls2 = []
        for time in light_forcast2:
            flt = self.wc2.convert_timedelta_to_float(time)
            temp_ls2.append(flt)

        #[7.1625, 7.188055555555556, 7.213333333333334, 7.238055555555556, 7.263055555555556]

        average2 = self.wc1.calculate_average_hours(light_forcast2)
        # (7.1625 + 7.188055555555556 + 7.213333333333334 + 7.238055555555556 + 7.263055555555556) / 5 = 7.212999999999999

        self.assertEqual(average2, 7.212999999999999)
        self.assertIsInstance(average2, float)

    def test_calculate_water_interval(self):
        """This test is the main method of the Water Calculator class. This tests that a solar forcast of time is compiled, converted into floats, then averaged over the number of days. The final average represents the average light the plant is recieving during the current water period (the water interval).

        Based off of the plant's base light requirements and the current water schedule, a new water interval is calculated using a dictionary
        of thresholds. The water interval that is calculated is the plant's current water interval +/- the threshold."""

        water_interval1 = self.wc1.calculate_water_interval()
        # 1.The AVG for this plant's schedule is 12.152347222222222 hours per day in the current watering period.

        #2. The plant type's base light requirements are 14 hours per day of light.
        # We check the difference by average_hours - base_light: 12.152347222222222 - 14 = -1.84
        # A negative result means the plant is not recieving enough light. Therefore we need to increase the amount of time between watering to avoid overwatering this plant.

        #3. We use the negative_threshold calculations in this case and will pull the value from the threshold key that is true. res <= -1 and res > -3 therefore the current water schedule interval will increase by 1 days. 10 + 1 = 11

        #check that the new water interval is not below 0, and is not greater than the plant type's max days without water. Both are false so we will return 11.

        self.assertEqual(water_interval1, 11)

        water_interval2 = self.wc2.calculate_water_interval()
         # 1.The AVG for this plant's schedule is 7.212999999999999 hours per day in the current watering period.

        #2. The plant type's base light requirements are 4 hours per day of light.
        # We check the difference by average_hours - base_light: 7.212999999999999 - 4 = 3.21
        # A postive result means the plant is recieving enough, or possibly too much light. Therefore we need to decrease the amount of time between watering to prevent the plant from drying up.

        #3. We use the positive_threshold calculations in this case and will pull the value from the threshold key that is true. res >= 3 and res < 6   therefore the current water schedule interval will decrease by -2 days. 5 - 2 = 3

        #check that the new water interval is not below 0, and is not greater than the plant type's max days without water. Both are false so we will return 3.

        self.assertEqual(water_interval2, 3)