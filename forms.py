from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, DecimalField, SelectField, BooleanField
from wtforms.fields.html5 import DateField
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField, QuerySelectField, widgets
from wtforms.validators import InputRequired, Email, Length, EqualTo, DataRequired, Optional
from models import LightType, PlantType
from flask_wtf.file import FileField, FileAllowed

####################
# Signup/Login
# Forms
####################

class SignupForm(FlaskForm):
    """Form to sign up a new user."""

    city = StringField('City', validators=[InputRequired(message='You must enter your city for an accurate location.')], description='Seattle or Victoria')
    state = StringField('State or Territory')
    country = StringField('Country')
    name = StringField('Name', validators=[InputRequired(message='You must enter your name.')])
    email = StringField('E-mail', validators=[InputRequired(message='You must enter your email.'), Email(message='You must enter a valid email.')])
    username = StringField('Username', validators=[InputRequired(message='You must enter a username.')])
    password = PasswordField('Password', validators=[InputRequired(message='You must enter a password.'), Length(min=6, message='Your password must be greater than 6 characters.')])

class LoginForm(FlaskForm):
    """Form to login an existing user."""

    username = StringField('Username', validators=[InputRequired(message='You must enter your username.')])
    password = PasswordField('Password', validators=[Length(min=6, message='Your password must be greater than 6 characters.')])

####################
# Add Resources
# Forms
####################

class AddCollectionForm(FlaskForm):
    """Form for user to add a new Collection."""

    name = StringField('Collection Name', validators=[InputRequired('You must add a name for your collection')])

class AddRoomForm(FlaskForm):
    """Form for user to add a Room."""

    name = StringField('Room Name', validators=[InputRequired('You must add a name for your room')])

def light_types():
    """Get currently available light types from the LightType ORM."""
    return LightType.query.all()

class MultiCheckboxField(QuerySelectMultipleField):
    """
    A multiple-select, except displays a list of checkboxes.

    Iterating the field will produce subfields, allowing custom rendering of
    the enclosed checkbox fields.
    """
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class AddLightSource(FlaskForm):
    """Form to add light source(s) to a room."""

    light_type = MultiCheckboxField('Light Source', query_factory=light_types, get_label='type', blank_text='Select all of the light sources in your room.', validators=[DataRequired(message="You must select a light type.")])

def plant_types():
    """Get currently available plant types from the PlantType ORM."""
    return PlantType.query.all()

class AddPlantForm(FlaskForm):
    """Form to add a new plant."""

    name = StringField('Plant Name', validators=[InputRequired(message='You must enter a name for your plant.')])
    water_date = DateField('Water Date (If left blank this will default to today)', format='%Y-%m-%d', validators=[Optional()])
    image = FileField('Plant Image (Optional)', validators=[FileAllowed(['jpg', 'png', 'jpeg'], '.jpg, .png, or .jpeg images only!')])
    plant_type = QuerySelectField('Plant Type', query_factory=plant_types, get_label='name', allow_blank=True, blank_text='Select the type for your plant.', validators=[DataRequired(message="You must select a plant type.")])
    light_source = QuerySelectField('Light Source Type', get_label='type', allow_blank=True, blank_text='Select the light your plant uses.', validators=[DataRequired(message="You must select a light source.")]) 

####################
# Edit User
# Forms
####################

class EditLocationForm(FlaskForm):
    """Form for user to edit a user's location."""

    city = StringField('City', validators=[InputRequired(message='You must enter your city for an accurate location.')])
    state = StringField('State/Territory')
    country = StringField('Country')

class EditUserProfileForm(FlaskForm):
    """For to edit a user's profile."""

    name = StringField('Name', validators=[InputRequired(message='You must enter your name.')])
    username = StringField('Username', validators=[InputRequired(message='You must enter your username.')])
    email = StringField('E-mail', validators=[InputRequired(message='You must enter your email.'), Email(message='You must enter a valid email.')])
    password = PasswordField('Password', validators=[InputRequired(message='You must enter your password.')])

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

    name = StringField('Collection Name', validators=[InputRequired('You must add a name for your collection')])

class EditRoomForm(FlaskForm):
    """Form for user to edit a Room name."""

    name = StringField('Room Name', validators=[InputRequired('You must add a name for your room')])

class EditPlantForm(FlaskForm):
    """Form to edit a plant."""

    name = StringField('Plant Name', validators=[InputRequired(message='You must enter a name for your plant.')])
    image = FileField('Plant Image (Optional)', validators=[FileAllowed(['jpg', 'png', 'jpeg'], '.jpg, .png, or .jpeg images only!')])
    plant_type = QuerySelectField(query_factory=plant_types, get_label='name', allow_blank=True, blank_text='Select the type for your plant.', validators=[DataRequired(message='You must enter a plant type!.')])
    light_source = QuerySelectField(get_label='type', allow_blank=True, blank_text='Select the light your plant uses.', validators=[DataRequired(message='You must enter a light source!')])

    #Can I set a default option from the OBJ?

####################
# Schedule
# Forms
####################

class AddWaterHistoryNotes(FlaskForm):
    """A form for a user to add notes about a plant's health or condition."""

    notes = TextAreaField('Notes', validators=[Length(max=200, message="Notes must be less than 200 characters in length.")])

class EditWaterScheduleForm(FlaskForm):
    """Form to manually set a Water Schedule timeline."""

    manual_mode = BooleanField('Manual mode enabled?')
    water_interval = StringField('Watering Interval (in days)', validators=[InputRequired(message='You must set the number of days between waterings.')])