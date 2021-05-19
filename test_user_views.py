"""User View tests."""

# FLASK_ENV=production python3 -m unittest test_user_views.py

import os
from unittest import TestCase
from models import *
from decimal import *

#set DB environment to test DB
os.environ['DATABASE_URL'] = 'postgresql:///water_mate_test'

from app import *

#disable WTForms CSRF validation
app.config['WTF_CSRF_ENABLED'] = False

class TestUserViews(TestCase):
    """Test User Views in App."""

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
        plant2 = Plant(id=2, name='Cactus', image=None, user_id=1200, type_id=16, room_id=2, light_id=2)
        db.session.add_all([plant1, plant2])
        db.session.commit()
    
    def tearDown(self):
        """Rollback any sessions."""

        db.session.rollback()
        db.session.remove()
    
    def test_user_creation(self):
        """Test that a new user was created."""

        self.assertIsNotNone(self.user1)
        self.assertIsInstance(self.user1, User)

        self.assertIsNotNone(self.user2)
        self.assertIsInstance(self.user2, User)
    
    def test_view_dashboard(self):
        """The dashboard should display all of the user's collections, rooms, light sources, and plants."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user2.id
            
            res = c.get('/dashboard')

            self.assertEqual(res.status_code, 200)
            self.assertIn('Welcome to the dashboard, Kittenz Meow.', str(res.data))
            self.assertIn('My House', str(res.data))
            self.assertIn('Bedroom', str(res.data))
            self.assertIn('Southwest', str(res.data))
            self.assertIn('Cactus', str(res.data))

    
    def test_view_profile(self):
        """Test that the user profile view shows the user details."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.get('/profile')
        
            self.assertEqual(res.status_code, 200)
            self.assertIn('Pepper Cat', str(res.data))
            self.assertIn('peppercat@gmail.com', str(res.data))
            self.assertIn('peppercat', str(res.data))
            self.assertIn('Home', str(res.data))
    
    def test_view_edit_profile(self):
        """Test that the edit profile form displays and the default user data is present."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user2.id
            
            res = c.get('/profile/edit')

            self.assertEqual(res.status_code, 200)
            self.assertIn('Kittenz Meow', str(res.data))
            self.assertIn('kittenz@gmail.com', str(res.data))
            self.assertIn('kittenz', str(res.data))
            self.assertIn('Save', str(res.data))
    
    def test_edit_profile(self):
        """Test that the user profile is edited on submission."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user2.id
            
            res = c.post('/profile/edit', data={'name': 'Kittenz Meow', 'username': 'kittenzmeow', 'email': 'kittenzmeow@gmail.com', 'password': 'meowmeow'}, follow_redirects=True)

            updated_user = User.query.get(self.user2.id)

            self.assertEqual(res.status_code, 200)
            self.assertEqual(updated_user.username, 'kittenzmeow')
            self.assertEqual(updated_user.email, 'kittenzmeow@gmail.com')
    
    def test_view_edit_password(self):
        """Test the form loads to edit a password."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.get('/profile/edit-password')

            self.assertEqual(res.status_code, 200)
            self.assertIn('Edit Your Password', str(res.data))
            self.assertIn('Current Password', str(res.data))
            self.assertIn('New Password', str(res.data))
            self.assertIn('Confirm New Password', str(res.data))
            self.assertIn('Save', str(res.data))
    
    def test_edit_password(self):
        """Test a user's password is updated on submission."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.post('/profile/edit-password', data={'current_password': 'meowmeow', 'new_password': 'ilovefish', 'confirm_password': 'ilovefish'}, follow_redirects=True)

            updated_user = User.query.get(self.user1.id)

            self.assertEqual(res.status_code, 200)
            self.assertNotEqual(updated_user.password, '$2b$12$bSMrTNZoa.S8C/xmrTnLb.w7FovABWQ.0hUb4BuWizuzydaUiHp2m')
    
    def test_view_edit_location(self):
        """Test that a form loads to change a user's location."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user2.id
            
            res = c.get('/profile/edit-location')

            self.assertEqual(res.status_code, 200)
            self.assertIn('Edit Your Location', str(res.data))
            self.assertIn('City', str(res.data))
            self.assertIn('State/Territory', str(res.data))
            self.assertIn('Country', str(res.data))
            self.assertIn('Save', str(res.data))
    
    def test_edit_location(self):
        """Test that a user's location is updated on form submission."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user2.id
            
            res = c.post('/profile/edit-location', data={'city': 'Miami', 'state': 'FL', 'country': 'USA'}, follow_redirects=True)

            updated_user = User.query.get(self.user2.id)

            self.assertEqual(res.status_code, 200)
            self.assertEqual(updated_user.latitude, Decimal('25.774266'))
            self.assertEqual(updated_user.longitude, Decimal('-80.193659'))

    def test_delete_profile(self):
        """Test deleting a user's profile."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.post('/profile/delete', follow_redirects=True)

            users = User.query.all()
            collections = Collection.query.all()
            rooms = Room.query.all()
            lights = LightSource.query.all()
            plants = Plant.query.all()

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(users), 1)
            self.assertEqual(len(collections), 1)
            self.assertEqual(len(rooms), 1)
            self.assertEqual(len(lights), 1)
            self.assertEqual(len(plants), 1)