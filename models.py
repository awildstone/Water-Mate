"""SQLAlchemy models for Water Mate."""

from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()

def connect_db(app):
    """Connect this database to the Flask app.
    This method is called in the Flask app.
    """

    db.app = app
    db.init_app(app)


####################
# Organization Models
####################

class Collection(db.Model):
    """A Collection has a name, user id, and holds rooms."""

    __tablename__ = 'collection'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='cascade')) #delete if user is deleted

    rooms = db.relationship('room', backref='collection')


class Room(db.Model):
    """A Room has a name and holds plants and lightsources."""

    __tablename__ = 'room'

    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('collection.id', ondelete='cascade', nullable=False)) #nullable=False should raise an Integrity error if we try to delete a collection that contains rooms.

    plants = db.relationship('plant', backref='room')
    lightsources = db.relationship('lightsource', backref='room')

####################
# User Model
####################

class User(db.Model):
    """A User has an id, name, email, latitude, longitude, username, password, and type.
    The User class authenticates account and authorizes logins.
    The User class provides location data."""

    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, unique=True, nullable=False)
    latitude = db.Column(db.Numeric(8,6))
    longitude = db.Column(db.Numeric(9,6))
    username = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    type = db.Column(db.Text, nullable=False)

    collection = db.relationship('user')

    #create a class method to return the lat/long coordinates. We can access this through flask g User object


####################
# Plant Models
####################

class LightSource(db.Model):
    """A LightSource has a type, daily total (hours of light), room id, and location id."""

    __tablename__ = 'lightsource'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Text, nullable=False)
    daily_total = db.Column(db.Integer, nullable=False, default=8)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id', ondelete='cascade')) #delete if room is deleted
    
    #daily total needs to be calculated from the g user's location. get the location data from g user class to calculate daily total light.

    