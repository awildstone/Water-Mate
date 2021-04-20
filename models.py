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
    """A User has an id, name, email, latitude, longitude, username, password, and permissions
    A user holds one or more collections.
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

    collections = db.relationship('user')

    def __repr__(self):
        return f'<User #{self.id}: {self.username}, {self.email}>'
    
    def get_coordinates(self):
        """Get and return this user's coordinates."""
        return {
            "latitude": this.latitude,
            "longitude": this.longitude
        }
    
    #this should be handled in my signup route and just pass the lat & long into my signup method
    # def generate_coordindates(self, city, state, zipcode):
    #     """Generate the latitude and longitude coordindates with a user's city, state, zip."""
    
    #If I have time, lets explore if having a @property for password and using @password.setter is a better method for hashing/storing passwords https://www.patricksoftwareblog.com/password-hashing/

    @classmethod
    def signup(cls, name, email, latitude, longitude, username, password):
        """Sign up a new user and hash the user password. 
        Return the new user with hashed password."""
        
        salt = bcrypt.gensalt(rounds=12)
        hashed_pwd = bcrypt.generate_password_hash(password, salt).decode('UTF-8')

        new_user = User(
            name=name,
            email=email,
            latitude=latitude,
            longitude=longitude,
            username=username,
            pasword=hashed_pwd
        )

        db.session.add(new_user)
        return new_user
    
    @classmethod
    def authenticate(cls, username, password):
        """Locate the user in the DB for the respective username/password.
        If the user is not found, or fails to authenticte return False."""

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
            #pass user back to route to commit the session changes
            return user
        return False

####################
# Plant Models
####################

class LightType(db.Model):
    """A Light Type has 5 potential types that are immutatble for users. 
    Types are Artificial, North, East, South or West. """

    __tablename__ = 'light_type'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.Text, unique=True, nullable=False)

class LightSource(db.Model):
    """A LightSource has a type, daily total (hours of light), room id, and location id."""

    __tablename__ = 'light_source'

    id = db.Column(db.Integer, primary_key=True)
    type_id = db.Column(db.Integer, db.ForeignKey('light_type', nullable=False))
    daily_total = db.Column(db.Integer, nullable=False, default=8) #default is 8 for cases where artificial light source is used
    room_id = db.Column(db.Integer, db.ForeignKey('room.id', ondelete='cascade')) #delete if room is deleted

    plants = db.relationship('plant', backref='light')
    
    #daily total needs to be calculated from the g user's location & light type. get the location data from g user class to calculate daily total light for the relative location on earth. Adjust daily potential based off the conditions below for the type of light:

    #https://sciencepickle.com/earth-systems/coordinate-system/
    #Latitudes have positive and negative values. Northern Hemisphere latitudes are positive, and negative latitudes occur in the Southern Hemisphere
    #Northern hemisphere has lowsunlight in northern windows, while southern hemisphere has the most sunlight from northern windows.
    #In the Northern Hemisphere, north is to the left. The Sun rises in the east (far arrow), culminates in the south (to the right) while moving to the right, and sets in the west (near arrow). Both rise and set positions are displaced towards the north in midsummer and the south in midwinter.
    
    #Longitudes have positive and negative values. Positive longitudes are in the Eastern Hemisphere (east of the Prime Meridian), and negative occur in the Western Hemisphere (west of 0º).
    # In the Southern Hemisphere, south is to the left. The Sun rises in the east (near arrow), culminates in the north (to the right) while moving to the left, and sets in the west (far arrow). Both rise and set positions are displaced towards the south in midsummer and the north in midwinter.

    #in both southern and northern hemisphere we can asume that east facing windows recieve the most light in the morning up until the midday, and then west facing windows recieve the most light from midday to evening and the temps will be hotter.

 class PlantType(db.Model):
     """A PlantType has a name and base water schedule.
     A PlantType is immutable for Users and accessible to all Users to categorize plants."""

     __tablename__ = 'plant_type'

     id = db.Column(db.Integer, primary_key=True)
     name = db.Column(db.Text, unique=True, nullable=False)
     base_water = db.Column(db.Integer, nullable=False)

class Plant(db.Model):
    """A plant has a name, image, type, room, and waterschedule."""

    __tablename__ = 'plant'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text, nullable=False)
    image = db.Column(db.Text, nullable=False, default='/static/img/')
    type_id = db.Column(db.Integer, db.ForeignKey('plant_type'))
    room_id = db.Column(db.Integer, db.ForeignKey('room'))

    water_schedule = db.relationship('water_schedule', backref='plant')

class WaterSchedule(db.Model):
    """A Water Schedule has a next water date, plant id and holds a water history."""

    __tablename__ = 'water_schedule'

    id = db.Column(db.Integer, primary_key=True)
    next_date = db.Column(db.DateTime, nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey('plant', ondelete='cascade', nullable=False)) #if plant is deleted, delete schedule

    water_history = db.relationship('water_history', backref='water_schedule')

class WaterHistory(db.Model):
    """A Water History has a water date, snooze amount, notes, and a plant and water schedule id."""

    __tablename__ = 'water_history'

    id = db.Column(db.Integer, primary_key=True)
    water_date = db.Column(db.DateTime, nullable=False)
    snooze = db.Column(db.Integer)
    notes = db.Column(db.String(200))
    plant_id = db.Column(db.Integer, db.ForeignKey('plant', nullable=False))
    water_schedule_id = db.Column(db.Integer, db.ForeignKey('water_schedule', nullable=False))