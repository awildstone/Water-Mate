"""Flask App for Water Mate."""

import os
from flask import Flask, render_template, request, flash, redirect, session, g, url_for
from flask_debugtoolbar import DebugToolbarExtension #keep only for development
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
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False # for development only
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'J28r$CC&Z5NCN48O$CEe&749k')
#Disables Flask file caching
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
toolbar = DebugToolbarExtension(app) # for development only

connect_db(app)

####################
# Home/Pages/Error 
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

@app.route('/')
def homepage():
    """Show homepage."""

    if g.user:
        return render_template('home-authed.html')

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

    if form.validate_on_submit():
        try:
            new_user = User.signup(
                name=form.name.data,
                email=form.email.data,
                latitude=coords['lat'],
                longitude=coords['lng'],
                username=form.username.data,
                password=form.password.data
                )
            db.session.commit()

        except IntegrityError:
            flash('There was an error creating your account.', 'warning')
            return render_template('/user/signup.html', form=form)
        
        #add the new user to session
        session[CURRENT_USER_KEY] = new_user.id
        #remove the location variables from the session
        del session['location']

        flash(f'Welcome to Water Mate, {new_user.name}!', 'success')
        return redirect(url_for('get_started'))

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
            return redirect(url_for('dashboard'))
        
        flash('Invalid login credentials!', 'danger')

    return render_template('/user/login.html', form=form)

@app.route('/logout')
def logout():
    """Logout the current user."""

    if CURRENT_USER_KEY in session:
        del session[CURRENT_USER_KEY]

    flash("You have successfully logged out.", 'success')
    return redirect(url_for('login'))

####################
# User Routes
####################

@app.route('/get-started')
def get_started():
    """Show getting started page."""
    return render_template('get_started.html')

@app.route('/dashboard')
@auth_required
def dashboard():
    """Show the user dashboard for a specific user."""
    #this is probably the most complicated page to figure out the mechanics. I will come back to this page once the other routes are setup and functioning.
    user = g.user
    plants = user.plants

    return render_template('/user/dashboard.html', user=user, plants=plants)