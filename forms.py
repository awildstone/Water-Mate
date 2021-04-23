from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, DecimalField, SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField, QuerySelectField
from wtforms.validators import InputRequired, Email, Length, EqualTo, Required
from models import LightType, PlantType
from flask_wtf.file import FileField, FileAllowed

####################
# Signup/Login
# Forms
####################

class LocationForm(FlaskForm):
    """Form for user to set their location."""

    city = StringField('City', validators=[InputRequired(message='You must enter your city for an accurate location.')])
    state = StringField('State', validators=[InputRequired(message='You must enter your state for an accurate location.')])

class SignupForm(FlaskForm):
    """Form to sign up a new user."""

    name = StringField('Name', validators=[InputRequired(message='You must enter your name.')])
    email = StringField('E-mail', validators=[InputRequired(message='You must enter your email.'), Email(message='You must enter a valid email.')])
    # latitude = DecimalField('Latitude', places=6, validators=[InputRequired()])
    # longitude = DecimalField('Longitude', places=6, validators=[InputRequired()])
    username = StringField('Username', validators=[InputRequired(message='You must enter a username.')])
    password = PasswordField('Password', validators=[InputRequired(message='You must enter a password.'), Length(min=6, message='Your password must be greater than 6 characters.')])

class LoginForm(FlaskForm):
    """Form to login an existing user."""

    username = StringField('Name', validators=[InputRequired(message='You must enter your username.')]) #add logic in view to raise error if username does not exist
    password = PasswordField('Password', validators=[Length(min=6, message='Your password must be greater than 6 characters.')]) #add logic in view to raise error if password doesn't match.

####################
# Add Resources
# Forms
####################

class AddCollectionForm(FlaskForm):
    """Form for user to add a new Collection."""

    name = StringField('Collection Name', validators=[InputRequired('You must add a name for your collection')]) #add logic to view to raise error if collection name is not unique

class AddRoomForm(FlaskForm):
    """Form for user to add a Room."""

    name = StringField('Room Name', validators=[InputRequired('You must add a name for your room')]) #add logic to view to raise error if room name is not unique

def light_types():
    """Get currently available light types from the LightType ORM."""
    return LightType.query.all()

class AddLightSource(FlaskForm):
    """Form to add light source(s) to a room."""
    
    light_type = QuerySelectMultipleField('Light Source', query_factory=light_types, get_label='type', allow_blank=True, blank_text='Select all of the light sources in your room.') #this will return a list of lighttype ORM objects

def plant_types():
    """Get currently available plant types from the PlantType ORM."""
    return PlantType.query.all()

class AddPlantForm(FlaskForm):
    """Form to add a new plant."""

    name = StringField('Plant Name', validators=[InputRequired(message='You must enter a name for your plant.')])
    image = FileField('Plant Image (Optional)', validators=[FileAllowed(['jpg', 'png', 'jpeg'], '.jpg, .png, or .jpeg images only!')])
    plant_type = QuerySelectField('Plant Type', query_factory=plant_types, get_label='name', allow_blank=True, blank_text='Select the type for your plant.') #this will return the planttype ORM object
    light_source = QuerySelectField('Light Source Type', get_label='type') #need to explicitly pass the query for this Room's light sources from the route view https://wtforms.readthedocs.io/en/2.3.x/ext/

####################
# Edit User
# Forms
####################

class EditLocationForm(FlaskForm):
    """Form to edit a user's location."""

    city = StringField('City', validators=[InputRequired(message='You must enter your city for an accurate location.')])
    state = StringField('State', validators=[InputRequired(message='You must enter your state for an accurate location.')])
    zipcode = StringField('Zipcode (Optional)')


class EditUserProfileForm(FlaskForm):
    """For to edit a user's profile."""

    name = StringField('Name', validators=[InputRequired(message='You must enter your name.')])
    email = StringField('E-mail', validators=[InputRequired(message='You must enter your email.'), Email(message='You must enter a valid email.')]) #raise error if email is already taken in route view
    password = PasswordField('Password', validators=[InputRequired(message='You must enter your password.')]) #raise error in route if password doesn't match current pwd

class ChangePasswordForm(FlaskForm):
    """Form to change a user's password."""

    current_password = PasswordField('Current Password', validators=[InputRequired(message='You must enter your current password.')])
    new_password = PasswordField('New Password', validators=[InputRequired(message='You must enter your new password.'), EqualTo('confirm_password', message='New passwords must match.'), Length(min=6, message="New password must be at least 6 characters in length.")])
    confirm_password = PasswordField('Confirm New Password', validators=[InputRequired(message='You must enter your new password.'), Length(min=6, message="New password must be at least 6 characters in length.")])

####################
# Edit Resources
# Forms
####################

class EditCollectionForm(FlaskForm):
    """Form for user to edit a Collection name."""

    name = StringField('Collection Name', validators=[InputRequired('You must add a name for your collection')]) #add logic to view to raise error if collection name is not unique

class EditRoomForm(FlaskForm):
    """Form for user to edit a Room name."""

    name = StringField('Collection Name', validators=[InputRequired('You must add a name for your room')]) #add logic to view to raise error if room name is not unique

class EditPlantForm(FlaskForm):
    """Form to edit a plant."""

    name = StringField('Plant Name', validators=[InputRequired(message='You must enter a name for your plant.')])
    image = FileField('Plant Image (Optional)', validators=[FileAllowed(['jpg', 'png', 'jpeg'], '.jpg, .png, or .jpeg images only!')])
    plant_type = QuerySelectField(query_factory=plant_types, get_label='name', allow_blank=True, blank_text='Select the type for your plant.') #this will return the planttype ORM object
    light_source = QuerySelectField(get_label='type') #need to explicitly pass the query for this Room's light sources from the route view https://wtforms.readthedocs.io/en/2.3.x/ext/

####################
# Schedule
# Forms
####################

class AddWaterHistoryNotes(FlaskForm):
    """A form for a user to add notes about a plant's health or condition."""

    notes = TextAreaField('Notes', validators=[Length(max=200, message="Notes must be less than 200 characters in length.")])

# I found this solution to create a custom validator that checks if another field has a truthy value before showing the 2nd field condition:
# https://stackoverflow.com/questions/8463209/how-to-make-a-field-conditionally-optional-in-wtforms/44037077

class RequiredIf(Required):
    # a validator which makes a field required if
    # another field is set and has a truthy value

    def __init__(self, other_field_name, *args, **kwargs,):
        self.other_field_name = other_field_name
        super(RequiredIf, self).__init__(*args, **kwargs)

    def __call__(self, form, field):
        other_field = form._fields.get(self.other_field_name)
        if other_field is None:
            raise Exception('no field named "%s" in form' % self.other_field_name)
        if bool(other_field.data):
            super(RequiredIf, self).__call__(form, field)

class EditWaterScheduleForm(FlaskForm):
    """Form to manually set a Water Schedule timeline."""

    manual_mode = SelectField('Manual mode enabled?', choices=[(True, 'Yes'),(False, 'No')], coerce=bool, validators=[InputRequired(message='You must choose if manual mode is enabled.')])
    water_interval = StringField('Watering Interval (in days)', validators=[RequiredIf('manual_mode')])