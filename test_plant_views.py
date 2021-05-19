"""Test Plant Views."""

# FLASK_ENV=production python3 -m unittest test_plant_views.py

import os
from io import BytesIO
# from csv import DictReader
from unittest import TestCase
from models import *
from datetime import datetime, timedelta

#set DB environment to test DB
os.environ['DATABASE_URL'] = 'postgresql:///water_mate_test'

from app import *

#disable WTForms CSRF validation
app.config['WTF_CSRF_ENABLED'] = False

class TestPlantViews(TestCase):
    """A class to test plant views and functionality in the app."""

    def setUp(self):
        """Setup DB rows and clear any old data."""

        self.client = app.test_client()

        db.session.rollback()
        db.session.remove()

        #delete any old data from the tables
        db.session.query(WaterHistory).delete()
        db.session.commit()

        db.session.query(WaterSchedule).delete()
        db.session.commit()

        db.session.query(Plant).delete()
        db.session.commit()

        db.session.query(Collection).delete()
        db.session.commit()

        db.session.query(LightSource).delete()
        db.session.commit()

        db.session.query(Room).delete()
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

        self.user1.id = 1000
        db.session.commit()

        self.user2 = User.signup(
            name='Kittenz Meow',
            email='kittenz@gmail.com',
            latitude='45.520247',
            longitude='-122.674195',
            username='kittenz',
            password='meowmeow')

        self.user2.id = 1200
        db.session.commit()

        #set up test collections
        collection1 = Collection(id=1, name='Home', user_id=1000)
        collection2 = Collection(id=2, name='My House', user_id=1200)
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
        
        #set up test plants
        plant1 = Plant(id=1, name='Hoya', image=None, user_id=1000, type_id=37, room_id=1, light_id=1)
        db.session.add(plant1)
        db.session.commit()

        #set up test water schedule
        ws1 = WaterSchedule(id=1, water_date=datetime(2021, 5, 1), next_water_date=datetime(2021, 5, 1) + timedelta(days=7), water_interval=7, plant_id=1)
        db.session.add(ws1)
        db.session.commit()
    
    def tearDown(self):
        """Rollback any sessions."""
        db.session.rollback()
        db.session.remove()

        #delete the s3 folders that were created for test_add_plant and test_edit_plant
        s3 = boto3.resource('s3', aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'), aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
        bucket = s3.Bucket(BUCKET_NAME)
        for key in bucket.objects.filter(Prefix=f'uploads/user/{1000}/'):
            key.delete()
        for key in bucket.objects.filter(Prefix=f'uploads/user/{1200}/'):
            key.delete()

    def test_view_plant_details(self):
        """View a plant's details by plant ID."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.get('/collection/room/plant/1')
        
            self.assertEqual(res.status_code, 200)
            self.assertIn('Hoya', str(res.data))
            self.assertIn('/static/img/succulents.png', str(res.data))
            self.assertIn('Hoya Details', str(res.data))
            self.assertIn('Collection: Home', str(res.data))
            self.assertIn('Room: Kitchen', str(res.data))
            self.assertIn('Light Source: East', str(res.data))
            self.assertIn('Water Schedule For Hoya', str(res.data))
            self.assertIn('<b>Last Watered:</b> 05/01/2021', str(res.data))
            self.assertIn('<b>Watering Interval:</b> Every 7 days', str(res.data))
            self.assertIn('<b>Next Water Date:</b> 05/08/2021', str(res.data))
            self.assertIn('<b>Manual Mode enabled?</b> False', str(res.data))
    
    def test_add_plant_form(self):
        """Display a form to add a new plant."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user2.id
            
            res = c.get('/collection/rooms/2/add-plant')

            self.assertEqual(res.status_code, 200)
            self.assertIn('Add a new Plant', str(res.data))
            self.assertIn('Please use the form below to add a new plant to your Bedroom.', str(res.data))
            self.assertIn('Plant Name', str(res.data))
            self.assertIn('Plant Image (Optional)', str(res.data))
            self.assertIn('Plant Type', str(res.data))
            self.assertIn('Agave', str(res.data))
            self.assertIn('Monstera', str(res.data))
            self.assertIn('Sedum', str(res.data))
            self.assertIn('Light Source Type', str(res.data))
            self.assertIn('Southwest', str(res.data))
    
    def test_add_plant(self):
        """Add a new plant to a room/collection."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user2.id
            with open('/Users/aimeewildstone/Desktop/rdt.png', 'rb') as img:
                imgStringIO1 = BytesIO(img.read())

            #this test will create folders in the s3 bucket /uploads/user/1200/rdt.png
            res = c.post('/collection/rooms/2/add-plant', content_type='multipart/form-data', data={'name': 'Sansevieria Fernwood', 'water_date': '', 'image': (imgStringIO1, 'rdt.png'), 'plant_type': 28, 'light_source': 2}, follow_redirects=True)

            plants = Plant.query.filter_by(room_id=2).all()

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(plants), 1)
            self.assertIn('New plant, Sansevieria Fernwood, added to Bedroom!', str(res.data))
            self.assertIn('Sansevieria Fernwood', str(res.data))
    
    def test_edit_plant_form(self):
        """View a form to edit a plant."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.get('/collection/room/plant/1/edit')
        
            self.assertEqual(res.status_code, 200)
            self.assertIn('Edit Hoya', str(res.data))
            self.assertIn('Please enter the new details of your plant. All fields except for image upload are required.', str(res.data))
            self.assertIn('Plant Name', str(res.data))
            self.assertIn('Plant Image (Optional)', str(res.data))
            self.assertIn('Plant Type', str(res.data))
            self.assertIn('Light Source', str(res.data))
            self.assertIn('East', str(res.data))
    
    def test_edit_plant(self):
        """Edit a plan't details by plant ID."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            with open('/Users/aimeewildstone/Desktop/rdt.png', 'rb') as img:
                imgStringIO1 = BytesIO(img.read())
            
            #this test will create folders in the s3 bucket /uploads/user/1000/rdt.png
            res = c.post('/collection/room/plant/1/edit', data={'name': 'Hoya Publicayx', 'water_date': '2021-5-1', 'image': (imgStringIO1, 'rdt.png'), 'plant_type': 37, 'light_source': 1}, follow_redirects=True)

            self.assertEqual(res.status_code, 200)
            self.assertIn('Hoya Publicayx', str(res.data))
            self.assertIn('Hoya Publicayx updated!', str(res.data))
    
    def test_delete_plant(self):
        """Delete a plant by plant ID."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.post('/collection/room/plant/1/delete', follow_redirects=True)

            plants = Plant.query.all()

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(plants), 0)
            self.assertIn('Plant Deleted.', str(res.data))