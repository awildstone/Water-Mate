"""Flask App for Water Mate."""

import os
from flask import Flask, render_template, request, flash, redirect, session, g, url_for
from sqlalchemy.exc import IntegrityError
from functools import wraps
from models import db, connect_db, Collection, Room, User, LightType, LightSource, PlantType, Plant, WaterSchedule, WaterHistory
from forms import *
from werkzeug.utils import secure_filename #use for add/edit plant route to upload the image https://flask-wtf.readthedocs.io/en/stable/form.html
from location import UserLocation

CURRENT_USER_KEY = 'current_user'

app = Flask(__name__)

uri = os.getenv("DATABASE_URL", "postgresql:///water_mate")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = uri

# app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL', 'postgres:///water_mate'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'J28r$CC&Z5NCN48O$CEe&749k')
#Disables Flask file caching
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

connect_db(app)

####################
# Home/Pages/Error 
# Routes
####################

@app.route('/')
def homepage():
    """Show homepage."""
    return render_template('home.html')

@app.errorhandler(404)
def page_not_found(e):
    """404 not found."""
    return render_template('404.html', e=e), 404

@app.errorhandler(403)
def forbidden(e):
    """403 forbidden route."""
    return render_template("403.html", e=e), 403

@app.route('/about')
def about():
    """Show about page."""
    return render_template('about.html')

####################
# Signup/Login/Logout 
# Routes
####################

@app.before_request
def check_for_authed_user():
    """Check if there is a current user session before each request.
    If current user in session, add the user to the global g user."""

    if CURRENT_USER_KEY in session:
        g.user = User.query.get_or_404(session[CURRENT_USER_KEY])
    else:
        g.user = None

def auth_required(f):
    """This decorator function confirms the global g user is active before the request is processed."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not g.user:
            flash('Access unauthorized.', 'danger')
            return redirect(url_for('homepage'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/signup', methods=['GET', 'POST'])
def get_location():
    """Get a new user's location."""

    form = LocationForm()

    if form.validate_on_submit():

        user_location = UserLocation(city=form.city.data, state=form.state.data)
        coordinates = user_location.get_coordinates()

        if coordinates:
            session['location'] = coordinates
            return redirect(url_for('signup'))
        else:
            flash('There was an error fetching your geolocation, please try again.', 'warning')

    return render_template('/user/location.html', form=form)

@app.route('/signup-user', methods=['GET', 'POST'])
def signup():
    """Signup a new user."""

    form = SignupForm()

    coords = session['location']
    latitude = coords['lat']
    longitude = coords['lng']

    if form.validate_on_submit():
        try:
            new_user = User.signup(
                name=form.name.data,
                email=form.email.data,
                latitude=latitude,
                longitude=longitude,
                username=form.username.data,
                password=form.password.data
                )
            db.session.commit()
        except IntegrityError:
            flash('There was an error creating your account.', 'warning')
            return render_template('/user/signup.html', form=form)
        
        #add the new user to session
        session[CURRENT_USER_KEY] = new_user.id
        flash(f'Welcome to Water Mate, {new_user.name}!', 'success')
        return redirect(url_for('homepage'))

    return render_template('/user/signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login an existing user."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(username=form.username.data, password=form.password.data)

        if user:
            #add the new user to session
            session[CURRENT_USER_KEY] = user.id
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('homepage'))
        
        flash('Invalid login credentials!', 'danger')

    return render_template('/user/login.html', form=form)

@app.route('/logout')
def logout():
    """Logout the current user."""

    if CURRENT_USER_KEY in session:
        del session[CURRENT_USER_KEY]

    flash("You have successfully logged out.", 'success')
    return redirect(url_for('login'))