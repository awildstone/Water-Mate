"""Room view tests."""

# FLASK_ENV=production python -m unittest test_room_views.py

import os
import shutil
from unittest import TestCase
from models import db, connect_db, User, Collection, Room, LightSource, Plant

#set DB environment to test DB
os.environ['DATABASE_URL'] = 'postgresql:///water_mate_test'

from app import app, CURRENT_USER_KEY, UPLOAD_FOLDER

#disable WTForms CSRF validation
app.config['WTF_CSRF_ENABLED'] = False

class TestRoomViews(TestCase):
    """A class to test room views in the app."""

    def setUp(self):
        """Setup DB rows and clear any old data."""

        self.client = app.test_client()

        #delete user's uploads folder & files
        if os.path.isdir(f'{UPLOAD_FOLDER}/{10}'):
            shutil.rmtree(f'{UPLOAD_FOLDER}/{10}')

        if os.path.isdir(f'{UPLOAD_FOLDER}/{12}'):
            shutil.rmtree(f'{UPLOAD_FOLDER}/{12}')

        #delete any old data from the tables
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
        collection2 = Collection(id=2, name='My Collection', user_id=12)
        db.session.add_all([collection1, collection2])
        db.session.commit()

        #set up test rooms
        room1 = Room(id=1, name='Kitchen', collection_id=1)
        room2 = Room(id=2, name='Bedroom', collection_id=1)
        room3 = Room(id=3, name='Bedroom', collection_id=2)
        room4 = Room(id=4, name='Bathroom', collection_id=2)
        db.session.add_all([room1, room2, room3, room4])
        db.session.commit()

        #set up test light source
        light_source1 = LightSource(id=1, type='East', type_id=3, daily_total=8, room_id=1)
        db.session.add(light_source1)
        db.session.commit()

        #set up test plant
        plant1 = Plant(id=1, name='Hoya', image=None, user_id=10, type_id=37, room_id=1, light_id=1)
        db.session.add(plant1)
        db.session.commit()
    
    def tearDown(self):
        """Rollback any sessions."""

        db.session.rollback()
        db.session.remove()
    
    def test_view_rooms(self):
        """Test viewing the rooms inside a collection."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.get('/collections/1')

            self.assertEqual(res.status_code, 200)
            self.assertIn('Home', str(res.data))
            self.assertIn('Kitchen', str(res.data))
            self.assertIn('Bedroom', str(res.data))
    
    def test_view_room(self):
        """Test viewing a single room."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user2.id
            
            res = c.get('/collection/rooms/4')

            self.assertEqual(res.status_code, 200)
            self.assertIn('Bathroom', str(res.data))
            self.assertIn('Add a Light Source', str(res.data))

    def test_add_room_form(self):
        """View the add room form."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id

            res = c.get('/collections/1/add-room')

            self.assertEqual(res.status_code, 200)
            self.assertIn('Add a new Room', str(res.data))
            self.assertIn('Please enter the name of your new Room.', str(res.data))
    
    def test_add_room(self):
        """Add a new room."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.post('/collections/1/add-room', data={'name': 'Living Room'}, follow_redirects=True)

            rooms = Room.query.filter_by(collection_id=1).all()

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(rooms), 3)
            self.assertIn('Living Room', str(res.data))
            self.assertIn('Kitchen', str(res.data))
            self.assertIn('Bedroom', str(res.data))
    
    def test_edit_room_form(self):
        """View edit room form."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user2.id

            res = c.get('/collection/rooms/4/edit')

            self.assertEqual(res.status_code, 200)
            self.assertIn('Edit Room', str(res.data))
            self.assertIn('Please enter the new name of your room.', str(res.data))
            self.assertIn('Bathroom', str(res.data))
    
    def test_edit_room(self):
        """Edit a room."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user2.id

            res = c.post('/collection/rooms/4/edit', data={'name': 'Office'}, follow_redirects=True)

            modified = Room.query.filter_by(id=4).first()

            self.assertEqual(res.status_code, 200)
            self.assertEqual(modified.name, 'Office')
    
    def test_delete_room(self):
        """Delete a room by id."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.post('/collection/rooms/2/delete', follow_redirects=True)

            rooms = Room.query.filter_by(collection_id=1).all()

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(rooms), 1)
    
    def test_delete_room_with_plants(self):
        """You cannot delete a room that has plants in it."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.post('/collection/rooms/2/delete', follow_redirects=True)

            rooms = Room.query.filter_by(collection_id=1).all()

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(rooms), 2)