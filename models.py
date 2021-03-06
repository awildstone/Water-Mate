"""SQLAlchemy models for Water Mate."""

from datetime import datetime
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

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

    __tablename__ = 'collections'
    __table_args__ = (db.UniqueConstraint('user_id', 'name'),)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='cascade'))

    rooms = db.relationship('Room', backref='collection', cascade='all, delete-orphan')

class Room(db.Model):
    """A Room has a name, a collection id, and holds plants and lightsources."""

    __tablename__ = 'rooms'
    __table_args__ = (db.UniqueConstraint('collection_id', 'name'),)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    collection_id = db.Column(db.Integer, db.ForeignKey('collections.id', ondelete='cascade'), nullable=False)

    plants = db.relationship('Plant', backref='room')
    lightsources = db.relationship('LightSource', backref='room', cascade='all, delete-orphan')

####################
# User Model
####################

class User(db.Model):
    """A User has an id, name, email, latitude, longitude, username, password, and permissions
    A user holds one or more collections.
    The User class authenticates account and authorizes logins.
    The User class provides location data."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    email = db.Column(db.Text, nullable=False)
    latitude = db.Column(db.Numeric(8,6))
    longitude = db.Column(db.Numeric(9,6))
    username = db.Column(db.Text, unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)

    collections = db.relationship('Collection', backref='user', cascade='all, delete-orphan')
    plants = db.relationship('Plant')

    def __repr__(self):
        return f'<User #{self.id}: {self.username}, {self.email}>'
    
    @property
    def get_coordinates(self):
        """Get and return this user's coordinates."""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude
        }
    
    #If I have time, lets explore if having a @property for password and using @password.setter is a better method for hashing/storing passwords https://www.patricksoftwareblog.com/password-hashing/

    @classmethod
    def signup(cls, name, email, latitude, longitude, username, password):
        """Sign up a new user and hash the user password. 
        Return the new user with hashed password."""
        
        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        new_user = User(
            name=name,
            email=email,
            latitude=latitude,
            longitude=longitude,
            username=username,
            password=hashed_pwd
        )

        db.session.add(new_user)
        return new_user
    
    @classmethod
    def authenticate(cls, username, password):
        """Locate the user in the DB for the respective username/password.
        If the user is not found, or fails to authenticate return False."""

        user = User.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user
        return False
    
    @classmethod
    def changePassword(cls, user, curr_password, new_password):
        """ Validates that the current password is correct, and updates to new password if correct.
        Returns False if the current password fails to authenticate."""

        is_auth = user.authenticate(user.username, curr_password)

        if is_auth:
            new_hashed_pwd = bcrypt.generate_password_hash(new_password).decode('UTF-8')
            user.password = new_hashed_pwd
            return user
        return False

####################
# Light Models
####################

class LightType(db.Model):
    """A Light Type has 9 potential types that are immutatble for users. 
    Types are Artificial, North, East, South, West, Northeast, Northwest, Southeast, Southwest. """

    __tablename__ = 'light_types'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Text, unique=True, nullable=False)

class LightSource(db.Model):
    """A LightSource has a type, daily total (hours of light), room id, and location id."""

    __tablename__ = 'light_sources'
    __table_args__ = (db.UniqueConstraint('type_id', 'room_id'),)

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Text, db.ForeignKey('light_types.type'), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('light_types.id'), nullable=False)
    daily_total = db.Column(db.Integer, nullable=False, default=8) #default is 8 for cases where artificial light source is used
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id', ondelete='cascade'))

####################
# Plant Models
####################

class PlantType(db.Model):
    """A PlantType has a name and base water schedule.
    A PlantType is immutable for Users and accessible to all Users to categorize plants."""

    __tablename__ = 'plant_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, unique=True, nullable=False)
    base_water = db.Column(db.Integer, nullable=False)
    base_sunlight = db.Column(db.Integer, nullable=False)
    max_days_without_water = db.Column(db.Integer, nullable=False)

    plants = db.relationship('Plant', backref='type')

class Plant(db.Model):
    """A plant has a name, image, type, room, and waterschedule."""

    __tablename__ = 'plants'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    image = db.Column(db.Text, nullable=False, default='/static/img/succulents.png')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type_id = db.Column(db.Integer, db.ForeignKey('plant_types.id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('rooms.id'), nullable=False)
    light_id = db.Column(db.Integer, db.ForeignKey('light_sources.id'), nullable=False)

    water_schedule = db.relationship('WaterSchedule', backref='plant', cascade='all, delete-orphan')
    light = db.relationship('LightSource', backref='plant')

####################
# Schedule Models
####################

class WaterSchedule(db.Model):
    """A Water Schedule has a next water date, plant id and holds a water history."""

    __tablename__ = 'water_schedules'

    id = db.Column(db.Integer, primary_key=True)
    water_date = db.Column(db.DateTime, nullable=False)
    next_water_date = db.Column(db.DateTime, nullable=False)
    water_interval = db.Column(db.Integer, nullable=False)
    manual_mode = db.Column(db.Boolean, nullable=False, default=False)
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.id', ondelete='cascade'), nullable=False)

    water_history = db.relationship('WaterHistory', backref='water_schedule', cascade='all, delete-orphan')

    @property
    def get_water_date(self):
        """Gets the current water_date and returns a string representation."""
        return self.water_date.strftime("%m/%d/%Y")
    
    @property
    def get_next_water_date(self):
        """Gets the current water_date and returns a string representation."""
        return self.next_water_date.strftime("%m/%d/%Y")

class WaterHistory(db.Model):
    """A Water History has a water date, snooze amount, notes, and a plant and water schedule id."""

    __tablename__ = 'water_history'

    id = db.Column(db.Integer, primary_key=True)
    water_date = db.Column(db.DateTime, nullable=False)
    snooze = db.Column(db.Integer)
    notes = db.Column(db.String(200), nullable=False, default='No notes added.')
    plant_id = db.Column(db.Integer, db.ForeignKey('plants.id'), nullable=False)
    water_schedule_id = db.Column(db.Integer, db.ForeignKey('water_schedules.id', ondelete='cascade'), nullable=False)

    @property
    def get_water_date(self):
        """Gets the current water_date and returns a string representation."""
        return self.water_date.strftime("%m/%d/%Y, %H:%M:%S")