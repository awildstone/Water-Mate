"""Schedule View Tests."""

# FLASK_ENV=production python -m unittest test_schedule_views.py

import os
import shutil
from unittest import TestCase
from models import db, connect_db, User, Collection, Room, LightSource, Plant, WaterSchedule, WaterHistory
from datetime import datetime, timedelta, date

#set DB environment to test DB
os.environ['DATABASE_URL'] = 'postgresql:///water_mate_test'

from app import app, CURRENT_USER_KEY, UPLOAD_FOLDER

#disable WTForms CSRF validation
app.config['WTF_CSRF_ENABLED'] = False

class TestScheduleViews(TestCase):
    """A class to test the schedule views and functionality in the app."""

    def setUp(self):
        """Setup DB rows and clear any old data."""

        self.client = app.test_client()

        #delete user's uploads folder & files
        if os.path.isdir(f'{UPLOAD_FOLDER}/{10}'):
            shutil.rmtree(f'{UPLOAD_FOLDER}/{10}')

        if os.path.isdir(f'{UPLOAD_FOLDER}/{12}'):
            shutil.rmtree(f'{UPLOAD_FOLDER}/{12}')

        #delete any old data from the tables
        db.session.query(WaterSchedule).delete()
        db.session.commit()

        db.session.query(Plant).delete()
        db.session.commit()

        db.session.query(LightSource).delete()
        db.session.commit()

        db.session.query(Room).delete()
        db.session.commit()

        db.session.query(Collection).delete()
        db.session.commit()

        db.session.query(User).delete()
        db.session.commit()

        #set up test user accounts
        self.user1 = User.signup(
            name='Pepper Cat',
            email='peppercat@gmail.com',
            latitude='47.466748',
            longitude='-122.34722',
            username='peppercat',
            password='meowmeow')

        self.user1.id = 10
        if not os.path.isdir(f'{UPLOAD_FOLDER}/{self.user1.id}'):
            os.makedirs(f'{UPLOAD_FOLDER}/{self.user1.id}')

        self.user2 = User.signup(
            name='Kittenz Meow',
            email='kittenz@gmail.com',
            latitude='45.520247',
            longitude='-122.674195',
            username='kittenz',
            password='meowmeow')

        self.user2.id = 12
        if not os.path.isdir(f'{UPLOAD_FOLDER}/{self.user2.id}'):
            os.makedirs(f'{UPLOAD_FOLDER}/{self.user2.id}')

        db.session.commit()

        #set up test collections
        collection1 = Collection(id=1, name='Home', user_id=10)
        collection2 = Collection(id=2, name='My House', user_id=12)
        db.session.add_all([collection1, collection2])
        db.session.commit()

        #set up test rooms
        room1 = Room(id=1, name='Kitchen', collection_id=1)
        room2 = Room(id=2, name='Bedroom', collection_id=2)
        db.session.add_all([room1, room2])
        db.session.commit()

        #set up test light sources
        light_source1 = LightSource(id=1, type='East', type_id=3, daily_total=8, room_id=1)
        light_source2 = LightSource(id=2, type='Southwest', type_id=9, daily_total=8, room_id=2)
        db.session.add_all([light_source1, light_source2])
        db.session.commit()
    
    def tearDown(self):
        """Rollback any sessions."""

        db.session.rollback()
        db.session.remove()
    
    def test_create_water_schedule(self):
        """Test that a new water schedule is created when a new plant is created."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.post('/collection/rooms/1/add-plant', data={'name': 'Sansevieria Fernwood', 'plant_type': 28, 'light_source': 1}, follow_redirects=True)

            plants = Plant.query.filter_by(room_id=1).all()

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(plants), 1)
            self.assertIn('Sansevieria Fernwood', str(res.data))
            self.assertIn('New plant, Sansevieria Fernwood, added to Kitchen!', str(res.data))

            ws = WaterSchedule.query.all()
            self.assertEqual(len(ws), 1)
            self.assertEqual(ws[0].plant_id, plants[0].id)
    
    def test_view_water_manager(self):
        """Test that the Water Manager only shows plants that are ready to water today."""

        #new plant that is not ready to water.
        plant1 = Plant(id=1, name='Hoya', user_id=10, type_id=37, room_id=1, light_id=1)
        ws1 = WaterSchedule(id=1, water_date=datetime(2021, 5, 1), next_water_date=datetime(2021, 5, 1) + timedelta(days=7), water_interval=7, plant_id=1)

        #new plant that is ready to water.
        plant2 = Plant(id=2, name='Calathea', user_id=10, type_id=17, room_id=1, light_id=1)
        ws2 = WaterSchedule(id=2, water_date=datetime(2021, 5, 1), next_water_date=datetime(2021, 5, 5), water_interval=7, plant_id=2)

        db.session.add_all([plant1, plant2, ws1, ws2])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id

            res = c.get('/water-manager')
            self.assertEqual(res.status_code, 200)
            self.assertIn('Calathea', str(res.data))
            self.assertNotIn('Hoya', str(res.data))

    def test_water_plant(self):
        """Test that a plant's water schedule is updated when a plant is watered."""

        #new plant that is ready to water.
        plant2 = Plant(id=2, name='Calathea', user_id=10, type_id=17, room_id=1, light_id=1)
        ws2 = WaterSchedule(id=2, water_date=datetime(2021, 5, 1), next_water_date=datetime(2021, 5, 5), water_interval=7, plant_id=2)

        db.session.add_all([plant2, ws2])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.post('/water-manager/2/water', json={'notes': 'Watering my test Calathea!'}, follow_redirects=True)

            self.assertEqual(res.status_code, 201)
            self.assertEqual({"status": "OK"}, res.json)

            ws = WaterSchedule.query.get(2)
            #because the timestamps must be exact, we'll just check that both dates in the schedule changed
            self.assertNotEqual(ws.water_date, datetime(2021, 5, 1))
            self.assertNotEqual(ws.next_water_date, datetime(2021, 5, 5))
            #check that the water interval changed
            self.assertNotEqual(ws.water_interval, 7)
    
    def test_water_plant_history(self):
        """Test that a Water History is created when a plant is watered."""

        #new plant that is ready to water.
        plant2 = Plant(id=2, name='Calathea', user_id=10, type_id=17, room_id=1, light_id=1)
        ws2 = WaterSchedule(id=2, water_date=datetime(2021, 5, 1), next_water_date=datetime(2021, 5, 5), water_interval=7, plant_id=2)

        db.session.add_all([plant2, ws2])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.post('/water-manager/2/water', json={'notes': 'Watering my test Calathea!'}, follow_redirects=True)

            wh = WaterHistory.query.filter_by(plant_id=2).first()
            ws = WaterSchedule.query.get(2)

            self.assertEqual(res.status_code, 201)
            self.assertEqual({"status": "OK"}, res.json)
            self.assertEqual(wh.notes, 'Watering my test Calathea!')
            self.assertEqual(wh.water_date, ws.water_date)
    
    def test_snooze_plant(self):
        """Test that a plant's water schedule is updated when a plant is snoozed."""

        #new plant that is ready to water.
        plant1 = Plant(id=1, name='Hoya', user_id=12, type_id=37, room_id=2, light_id=2)
        ws1 = WaterSchedule(id=1, water_date=datetime(2021, 5, 1), next_water_date=datetime.today(), water_interval=10, plant_id=1)

        db.session.add_all([plant1, ws1])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user2.id
            
            res = c.post('/water-manager/1/snooze', json={'notes': 'Watering my test Hoya!'}, follow_redirects=True)

            self.assertEqual(res.status_code, 201)
            self.assertEqual({"status": "OK"}, res.json)

            ws = WaterSchedule.query.get(1)
            #next water date should increase by 3, and current water date should remain the same
            self.assertEqual(ws.water_date, datetime(2021, 5, 1))
            self.assertEqual(ws.next_water_date.day, (datetime.today() + timedelta(days=3)).day)


    def test_snooze_plant_history(self):
        """Test that a Water History is created when a plant is snoozed."""

        #new plant that is ready to water.
        plant1 = Plant(id=1, name='Hoya', user_id=12, type_id=37, room_id=2, light_id=2)
        ws1 = WaterSchedule(id=1, water_date=datetime(2021, 5, 1), next_water_date=datetime.today(), water_interval=10, plant_id=1)

        db.session.add_all([plant1, ws1])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user2.id
            
            res = c.post('/water-manager/1/snooze', json={'notes': 'Watering my test Hoya!'}, follow_redirects=True)

            self.assertEqual(res.status_code, 201)
            self.assertEqual({"status": "OK"}, res.json)

            ws = WaterSchedule.query.get(1)
            wh = WaterHistory.query.filter_by(plant_id=1).first()
    
            self.assertEqual(wh.notes, 'Watering my test Hoya!')
            self.assertEqual(wh.water_date, ws.water_date)
    
    def test_edit_water_schedule_form(self):
        """View a form to edit a Water Schedule."""

        #new plant that is ready to water.
        plant1 = Plant(id=1, name='Hoya', user_id=12, type_id=37, room_id=2, light_id=2)
        ws1 = WaterSchedule(id=1, water_date=datetime(2021, 5, 1), next_water_date=datetime(2021, 5, 10), water_interval=10, plant_id=1)

        db.session.add_all([plant1, ws1])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user2.id
            
            res = c.get('/collection/room/plant/1/water-schedule/edit')

            self.assertEqual(res.status_code, 200)
            self.assertIn('Edit Water Schedule For Hoya', str(res.data))
            self.assertIn('You can use this form to toggle the water schedule to manual or off manual mode, or simply change the number of days until the next water date.', str(res.data))
            self.assertIn('Manual mode enabled?', str(res.data))

    def test_edit_water_schedule(self):
        """Test that a water schedule's Manual Mode, Water Interval and Next Water Date change on update. Water date should remain the same."""

        #new plant that is ready to water.
        plant2 = Plant(id=2, name='Calathea', user_id=10, type_id=17, room_id=1, light_id=1)
        ws2 = WaterSchedule(id=2, water_date=datetime(2021, 5, 1), next_water_date=datetime(2021, 5, 5), water_interval=7, plant_id=2)

        db.session.add_all([plant2, ws2])
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.post('/collection/room/plant/2/water-schedule/edit', data={'manual_mode': True, 'water_interval': 10}, follow_redirects=True)

            ws = WaterSchedule.query.get(2)

            self.assertEqual(res.status_code, 200)
            self.assertIn('Water Schedule updated.', str(res.data))
            self.assertEqual(ws.manual_mode, True)
            self.assertEqual(ws.water_interval, 10)
            self.assertEqual(ws.next_water_date, datetime(2021, 5, 1) + timedelta(days=ws.water_interval))
            self.assertEqual(ws.water_date, datetime(2021, 5, 1))
    
    def test_view_water_history(self):
        """View a plant's water history table."""

        #new plant that is ready to water.
        plant1 = Plant(id=1, name='Hoya', user_id=12, type_id=37, room_id=2, light_id=2)
        ws1 = WaterSchedule(id=1, water_date=datetime(2021, 5, 1), next_water_date=datetime(2021, 5, 10), water_interval=10, plant_id=1)

        db.session.add_all([plant1, ws1])
        db.session.commit()

        #simulate that the plant has been watered by updating the Water Schedule and creating a water history.
        update_ws = WaterSchedule.query.get(1)
        update_ws.water_date = datetime(2021, 5, 10)
        update_ws.new_water_interval = 9
        update_ws.next_water_date = datetime(2021, 5, 19)
        db.session.commit()

        wh = WaterHistory(id=1, water_date=datetime(2021, 5, 10), notes='Watered my plant.', plant_id=1, water_schedule_id=1)
        db.session.add(wh)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user2.id
            
            res = c.get('/collection/room/plant/1/water-history')
            self.assertEqual(res.status_code, 200)
            self.assertIn('Water History For Hoya', str(res.data))
            self.assertIn('Watered', str(res.data))
            self.assertIn('05/10/2021', str(res.data))
            self.assertIn('Watered my plant.', str(res.data))

