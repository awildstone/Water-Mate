from flask_wtf import FlaskForm, QuerySelectMultipleField, QuerySelectField
from wtforms import StringField, PasswordField, TextAreaField, DecimalField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from models import LightType, PlantType, Room
from flask_wtf.file import FileField, FileAllowed

####################
# Signup/Login
# Forms
####################

class LocationForm(FlaskForm):
    """Form for user to set their location."""

    city = StringField('City', validators=[DataRequired(message='You must enter your city for an accurate location.')])
    state = StringField('State', validators=[DataRequired(message='You must enter your state for an accurate location.')])
    zipcode = StringField('Zipcode (Optional)')

class SignupForm(FlaskForm):
    """Form to sign up a new user."""

    name = StringField('Name', validators=[DataRequired(message='You must enter your name.')])
    email = StringField('E-mail', validators=[DataRequired(message='You must enter your email.'), Email(message='You must enter a valid email.')])
    latitude = DecimalField('Latitude', validators=[DataRequired()])
    longitude = DecimalField('Longitude', validators=[DataRequired()])
    username = StringField('Name', validators=[DataRequired(message='You must enter a username.')])
    password = PasswordField('Password', validators=[DataRequired(message='You must enter a password.'), Length(min=6, message='Your password must be greater than 6 characters.')])

class LoginForm(FlaskForm):
    """Form to login an existing user."""

    username = StringField('Name', validators=[DataRequired(message='You must enter your username.')]) #add logic in view to raise error if username does not exist
    password = PasswordField('Password', validators=[Length(min=6, message='Your password must be greater than 6 characters.')]) #add logic in view to raise error if password doesn't match.

####################
# Add Resources
# Forms
####################

class AddCollectionForm(FlaskForm):
    """Form for user to add a new Collection."""

    name = StringField('Collection Name', validators=[DataRequired('You must add a name for your collection')]) #add logic to view to raise error if collection name is not unique

class AddRoomForm(FlaskForm):
    """Form for user to add a Room."""

    name = StringField('Collection Name', validators=[DataRequired('You must add a name for your room')]) #add logic to view to raise error if room name is not unique

def light_types():
    """Get currently available light types from the LightType ORM."""
    return LightType.query.all()

class AddLightSource(FlaskForm):
    """Form to add light source(s) to a room."""
    
    light_type = QuerySelectMultipleField(query_factory=light_types, get_lable=type, allow_blank=True, blank_text='Select all of the light sources in your room.') #this will return a list of lighttype ORM objects

def plant_types():
    """Get currently available plant types from the PlantType ORM."""
    return PlantType.query.all()

class AddPlant(FlaskForm):
    """Form to add a new plant."""
    name = StringField('Plant Name', validators=[DataRequired(message='You must enter a name for your plant.')])
    image = FileField('Plant Image (Optional)', validators=[FileAllowed(['jpg', 'png', 'jpeg'], '.jpg, .png, or .jpeg images only!')])
    plant_type = QuerySelectField(query_factory=plant_types, get_lable=name, allow_blank=True, blank_text='Select the type for your plant.') #this will return the planttype ORM object
    light_type = QuerySelectField(get_label='type') #need to explicitly pass the query for this Room's light sources from the route view https://wtforms.readthedocs.io/en/2.3.x/ext/

####################
# Edit User
# Forms
####################

class EditLocationForm(FlaskForm):
    """Form for user to edit their location."""

    city = StringField('City', validators=[DataRequired(message='You must enter your city for an accurate location.')])
    state = StringField('State', validators=[DataRequired(message='You must enter your state for an accurate location.')])
    zipcode = StringField('Zipcode (Optional)')


class EditUserProfile(FlaskForm):
    """."""
    name = StringField('Name', validators=[DataRequired(message='You must enter your name.')])
    email = StringField('E-mail', validators=[DataRequired(message='You must enter your email.'), Email(message='You must enter a valid email.')]) #raise error if email is already taken in route view
    password = PasswordField('Password', validators=[DataRequired(message='You must enter your password.')]) #raise error in route if password doesn't match current pwd

class ChangePasswordForm(FlaskForm):
    """Form to change a user's password."""

    current_password = PasswordField('Current Password', validators=[DataRequired(message='You must enter your current password.')])
    new_password = PasswordField('New Password', validators=[DataRequired(message='You must enter your new password.'), EqualTo('confirm_password', message='New passwords must match.'), Length(min=6, message="New password must be at least 6 characters in length.")])
    confirm_password = PasswordField('Confirm New Password', validators=[DataRequired(message='You must enter your new password.'), Length(min=6, message="New password must be at least 6 characters in length.")])

####################
# Edit Resources
# Forms
####################

#edit collection name
#edit room name
#edit light sources
#edit plant
#edit water schedule?