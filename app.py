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

@app.teardown_request
def teardown_request(exception):
    if exception:
        db.session.rollback()
    db.session.remove()

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
        
        session[CURRENT_USER_KEY] = new_user.id
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
            session[CURRENT_USER_KEY] = user.id
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(url_for('dashboard'))
        
        flash('Invalid login credentials!', 'danger')

    return render_template('/user/login.html', form=form)

@app.route('/logout')
@auth_required
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
@auth_required
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

#view user profile route
#edit user profile route
#edit user password route
#delete user account route

####################
# Collection Routes
####################

@app.route('/collections')
@auth_required
def show_collections():
    """Show user collection landing page."""

    collections = g.user.collections

    return render_template('/collection/all_collections.html', collections=collections)

@app.route('/collections/<int:collection_id>')
@auth_required
def view_collection(collection_id):
    """View a collection by id and all of the rooms inside the collection."""

    collection = Collection.query.get_or_404(collection_id)
    rooms = collection.rooms

    if collection.user_id != g.user.id:
        flash('Access Denied.', 'danger')
        return redirect(url_for('show_collections'))

    return render_template('/collection/collection.html', collection=collection, rooms=rooms)

@app.route('/collections/add-collection', methods=['GET', 'POST'])
@auth_required
def add_collection():
    """Add a new collection."""

    form = AddCollectionForm()

    if form.validate_on_submit():
        new_collection = Collection(
            name = form.name.data,
            user_id = g.user.id,
        )
        try:
            g.user.collections.append(new_collection)
            db.session.commit()
            flash(f'New Collection, {new_collection.name} - added!', 'success')
        except IntegrityError:
            flash('Collection names must be unique.', 'warning')

        return redirect(url_for('show_collections'))

    return render_template('/collection/add_collection.html', form=form)

@app.route('/collections/<int:collection_id>/edit', methods=['GET', 'POST'])
@auth_required
def edit_collection(collection_id):
    """Edit a collection by id."""

    collection = Collection.query.get_or_404(collection_id)

    form = EditCollectionForm(obj=collection)

    if g.user.id == collection.user_id:
        if form.validate_on_submit():
            try:
                collection.name = form.name.data
                db.session.commit()
                flash(f'{collection.name} updated!', 'success')
            except IntegrityError:
                flash('Collection names must be unique.', 'warning')
            return redirect(url_for('show_collections'))
    else:
        flash('Access Denied.', 'danger')
        return redirect(url_for('show_collections'))

    return render_template('/collection/edit_collection.html', form=form)

@app.route('/collections/<int:collection_id>/delete', methods=['POST'])
@auth_required
def delete_collection(collection_id):
    """Delete a collection by id."""

    collection = Collection.query.get_or_404(collection_id)

    if g.user.id == collection.user_id:
        try:
            db.session.delete(collection)
            db.session.commit()
            flash('Collection Deleted.', 'success')
        except IntegrityError:
            flash('You cannot delete a collection that has rooms!', 'warning')
    else:
        flash('Access Denied.', 'danger')
    
    return redirect(url_for('show_collections'))

####################
# Room Routes
####################

@app.route('/collection/rooms/<int:room_id>')
@auth_required
def view_room(room_id):
    """View a room by id."""

    room = Room.query.get_or_404(room_id)
    plants = room.plants
    lightsources = room.lightsources

    collection = Collection.query.get_or_404(room.collection_id)

    if collection.user_id != g.user.id:
        flash('Access Denied.', 'danger')
        return redirect(url_for('show_collections'))

    return render_template('/room/room.html', room=room, plants=plants, lightsources=lightsources)

@app.route('/collections/<int:collection_id>/add-room', methods=['GET', 'POST'])
@auth_required
def add_room(collection_id):
    """Add a new room to a collection."""

    form = AddRoomForm()

    collection = Collection.query.get_or_404(collection_id)

    if g.user.id == collection.user_id:
        if form.validate_on_submit():
            new_room = Room(
                name = form.name.data,
                collection_id = collection_id
            )
            try:
                collection.rooms.append(new_room)
                db.session.commit()
                flash(f'New Room, {new_room.name} - added!', 'success')
            except IntegrityError:

                flash('Room names must be unique.', 'warning')

            return redirect(url_for('view_collection', collection_id=collection_id))

    else:
        flash('Access Denied.', 'danger')
        return redirect(url_for('show_collections'))

    return render_template('/room/add_room.html', form=form)

@app.route('/collection/rooms/<int:room_id>/edit', methods=['GET', 'POST'])
@auth_required
def edit_room(room_id):
    """Edit a room by id."""

    room = Room.query.get_or_404(room_id)
    collection = Collection.query.get_or_404(room.collection_id)

    form = EditRoomForm(obj=room)

    if g.user.id == collection.user_id:
        if form.validate_on_submit():
            try:
                room.name = form.name.data
                db.session.commit()
                flash(f'{room.name} updated!', 'success')
            except IntegrityError:
                db.session.rollback() #For some reason my @app.teardown_request method isn't rolling back this session when it errors
                flash('Room names must be unique.', 'warning')
            return redirect(url_for('view_collection', collection_id=collection.id))
    else:
        flash('Access Denied.', 'danger')
        return redirect(url_for('view_collection', collection_id=collection.id))

    return render_template('/room/edit_room.html', form=form, room=room)

@app.route('/collection/rooms/<int:room_id>/delete', methods=['POST'])
@auth_required
def delete_room(room_id):
    """Delete a room by id."""

    room = Room.query.get_or_404(room_id)
    collection = Collection.query.get_or_404(room.collection_id)

    if g.user.id == collection.user_id:
        try:
            db.session.delete(room)
            db.session.commit()
            flash('Room Deleted.', 'success')
        except IntegrityError:
            flash('You cannot delete a room that has plants!', 'warning')
    else:
        flash('Access Denied.', 'danger')

    return redirect(url_for('view_collection', collection_id=collection.id))

####################
# Light Routes
####################

@app.route('/collection/rooms/<int:room_id>/add-light-source', methods=['GET', 'POST'])
@auth_required
def add_lightsource(room_id):
    """Add one or multiple light sources to a room."""

    form = AddLightSource()
    room = Room.query.get_or_404(room_id)
    collection = Collection.query.get_or_404(room.collection_id)

    if g.user.id == collection.user_id:
        if form.validate_on_submit():
            try:
                #types arrive as a list of ORM objects
                light_types = form.light_type.data

                for light in light_types:
                    #we will set the daily_total to the default 8 hours for now.
                    room.lightsources.append(LightSource(type=light.type, type_id=light.id, room_id=room_id))

                db.session.commit()
            except IntegrityError:
                flash('You already added this lightsource to this room!', 'warning')

            return redirect(url_for('view_room', room_id=room_id))
    else:
        flash('Access Denied.', 'danger')
        return redirect(url_for('view_collection', collection_id=collection.id))

    return render_template('/light/add_lightsource.html', form=form, room=room)

@app.route('/collection/room/lightsource/<int:lightsource_id>')
@auth_required
def view_lightsource_plants(lightsource_id):
    """View all of the plants that use this lightsource.
    Helpful if a user wants to delete a lightsource from a room 
    but needs to know which plants are assigned to this light."""

    lightsource = LightSource.query.get_or_404(lightsource_id)
    room = Room.query.get_or_404(lightsource.room_id)
    collection = Collection.query.get_or_404(room.collection_id)
    plants = lightsource.plant

    if g.user.id == collection.user_id:
        return render_template('/light/view_lightsource_plants.html', room=room, plants=plants, lightsource=lightsource)
    else:
        flash('Access Denied.', 'danger')
        return redirect(url_for('view_collection', collection_id=collection.id))

@app.route('/collection/room/lightsource/<int:lightsource_id>', methods=['POST'])
@auth_required
def delete_lightsource(lightsource_id):
    """Delete a lightsource from a room by id. 
    Lightsources that have plants using them cannot
    be deleted."""

    lightsource = LightSource.query.get_or_404(lightsource_id)
    room = Room.query.get_or_404(lightsource.room_id)
    collection = Collection.query.get_or_404(room.collection_id)

    if g.user.id == collection.user_id:
        try:
            db.session.delete(lightsource)
            db.session.commit()
            flash(f'{lightsource.type} light was deleted from your {room.name}', 'success')
        except IntegrityError:
            flash('You cannot delete a lightsource that has plants using it! Change your plant lightsource first.', 'warning')
        return redirect(url_for('view_room', room_id=room.id))
    else:
        flash('Access Denied.', 'danger')
        return redirect(url_for('view_collection', collection_id=collection.id))

####################
# Plant Routes
####################

#view a plant (name, type, lightsource, location(room), water schedule, link to schedule history?)
@app.route('/collection/room/plant/<int:plant_id>')
@auth_required
def view_plant(plant_id):
    """View a plants details by plant id. From the plant view you can
    edit plant details, view other details, or delete a plant."""

    plant = Plant.query.get_or_404(plant_id)
    room = Room.query.get_or_404(plant.room_id)
    collection = Collection.query.get_or_404(room.collection_id)

    if g.user.id == collection.user_id:
        return render_template('/plant/view_plant.html', plant=plant)
    else:
        flash('Access Denied.', 'danger')
        return redirect(url_for('view_collection', collection_id=collection.id))
        
#Add plant to room route
#Edit plant details (lightsource, room location, name, type, etc.)
#Delete plant from room route

####################
# Schedule Routes
####################

#View a plant's water schedule history
#Manually edit a plant's water frequency