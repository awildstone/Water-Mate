"""Collection View Tests."""

# FLASK_ENV=production python3 -m unittest test_collection_views.py

import os
from dotenv import load_dotenv
from unittest import TestCase
from models import *

#set DB environment to test DB
os.environ['DATABASE_URL'] = 'postgresql:///water_mate_test'

from app import *

#disable WTForms CSRF validation
app.config['WTF_CSRF_ENABLED'] = False

class TestCollectionViews(TestCase):
    """A class to test collection view route functionality in app."""

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

        self.user1.id = 10
        db.session.commit()

        self.user2 = User.signup(
            name='Kittenz Meow',
            email='kittenz@gmail.com',
            latitude='45.520247',
            longitude='-122.674195',
            username='kittenz',
            password='meowmeow')

        self.user2.id = 12
        db.session.commit()

        #set up test collections
        collection1 = Collection(id=1, name='Home', user_id=10)
        collection2 = Collection(id=2, name='Work', user_id=10)
        db.session.add_all([collection1, collection2])
        db.session.commit()

        #add a test room
        room1 = Room(id=1, name='Kitchen', collection_id=1)
        db.session.add(room1)
        db.session.commit()
    
    def tearDown(self):
        """Rollback any sessions."""
        db.session.rollback()
        db.session.remove()
    
    def test_view_collections(self):
        """View Collections."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.get('/collections')

            self.assertEqual(res.status_code, 200)
            self.assertIn('Your houseplant collections', str(res.data))
            self.assertIn('Home', str(res.data))
            self.assertIn('Work', str(res.data))
            self.assertIn('Add a Collection', str(res.data))
    
    def test_view_collection(self):
        """View a collection."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.get('/collections/1')

            self.assertEqual(res.status_code, 200)
            self.assertIn('Home', str(res.data))
            self.assertIn('Add a Room', str(res.data))
    
    def test_add_collection_form(self):
        """Show add a new collection form."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user2.id
            
            res = c.get('/collections/add-collection')

            self.assertEqual(res.status_code, 200)
            self.assertIn('Add a new Collection', str(res.data))
            self.assertIn('Your collection name can be anything you want (Home, Office, My Collection, etc.) but the name must be unique.', str(res.data))
            self.assertIn('Collection Name', str(res.data))
    
    def test_add_new_collection(self):
        """Add a new collection."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user2.id
            
            res = c.post('/collections/add-collection', data={'name': 'My Home', 'user_id': self.user2.id}, follow_redirects=True)

            collection = Collection.query.filter_by(user_id=12).first()

            self.assertEqual(res.status_code, 200)
            self.assertEqual(collection.name, 'My Home')
    
    def test_edit_collection_form(self):
        """View the edit collection form."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.get('/collections/2/edit')

            self.assertEqual(res.status_code, 200)
            self.assertIn('Edit Collection', str(res.data))
            self.assertIn('Collection Name', str(res.data))
            self.assertIn('Work', str(res.data))
    
    def test_edit_collection(self):
        """Test editing a collection name."""

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.post('/collections/2/edit', data={'name': 'My super awesome collection!!'}, follow_redirects=True)

            modified = Collection.query.get(2)
            self.assertEqual(res.status_code, 200)
            self.assertIn('My super awesome collection!!', str(res.data))
            self.assertEqual(modified.name, 'My super awesome collection!!')
    
    def test_delete_collection(self):
        """Test deleting a collection."""
        
        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id
            
            res = c.post('/collections/2/delete', follow_redirects=True)

            collections = Collection.query.all()

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(collections), 1)
            self.assertIn('Collection Deleted.', str(res.data))
    
    def test_delete_collection_with_plants(self):
        """You cannot delete a collection with plants in it."""
        light = LightSource(id=1, type='East', type_id=3, daily_total=8, room_id=1)
        db.session.add(light)
        db.session.commit()

        plant = Plant(id=1, name='Test', image='/static/img/succulents.png', user_id=10, type_id=28, room_id=1, light_id=1)
        db.session.add(plant)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as session:
                session[CURRENT_USER_KEY] = self.user1.id

            res = c.post('/collections/1/delete', follow_redirects=True)

            collections = Collection.query.all()

            self.assertEqual(res.status_code, 200)
            self.assertEqual(len(collections), 2)
            self.assertIn('You cannot delete a collection that has plants!', str(res.data))