"""Flask App for Water Mate."""

import os
import shutil
from flask import Flask, render_template, request, json, jsonify, flash, redirect, session, g, url_for, send_from_directory
from flask_debugtoolbar import DebugToolbarExtension #keep only for development
from sqlalchemy.exc import IntegrityError
from functools import wraps
from models import db, connect_db, Collection, Room, User, LightType, LightSource, PlantType, Plant, WaterSchedule, WaterHistory
from forms import *
from werkzeug.utils import secure_filename
from location import UserLocation
from datetime import datetime, timedelta
from water_calculator import WaterCalculator

CURRENT_USER_KEY = 'current_user'
UPLOAD_FOLDER = 'uploads/user'

app = Flask(__name__)

uri = os.getenv("DATABASE_URL", "postgresql:///water_mate")
if uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False # for development only
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'J28r$CC&Z5NCN48O$CEe&749k')
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0 #Disables Flask file caching
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
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
        if not g.user and not None:
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
def signup():
    """Get a user's geolocation and signup a new user."""

    form = SignupForm()

    if form.validate_on_submit():
        #get the user's geolocation
        user_location = UserLocation(city=form.city.data, state=form.state.data, country=form.country.data)
        coordinates = user_location.get_coordinates()

        if coordinates:
            #coordinates are valid, create a new user
            try:
                new_user = User.signup(
                    name=form.name.data,
                    email=form.email.data,
                    latitude=coordinates['lat'],
                    longitude=coordinates['lng'],
                    username=form.username.data,
                    password=form.password.data
                )
                db.session.commit()

                #create an uploads file directory for this user
                os.makedirs(f'{UPLOAD_FOLDER}/{new_user.id}')
                #add the new user to session
                session[CURRENT_USER_KEY] = new_user.id

                flash(f'Welcome to Water Mate, {new_user.name}!', 'success')
                return redirect(url_for('get_started'))

            except IntegrityError:
                flash('There was an error creating your account because the username was already taken. Please choose a different username.', 'warning')
                return render_template('/user/signup.html', form=form)
        else:
            flash('There was an error fetching your geolocation. Please check the spelling of your City or State/Country and try again.', 'warning')
            return redirect(url_for('signup'))

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
            return redirect(url_for('water_manager'))
        
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

@app.route('/profile')
@auth_required
def view_profile():
    """Show a user's profile details."""

    user = User.query.get_or_404(g.user.id)

    return render_template('/user/profile.html', user=user)

@app.route('/profile/edit', methods=['GET', 'POST'])
@auth_required
def edit_profile():
    """Edit a user's profile information."""

    form = EditUserProfileForm(obj=g.user)

    if form.validate_on_submit():
        if User.authenticate(g.user.username, form.password.data):
            try:
                user = User.query.get_or_404(g.user.id)
                user.name = form.name.data
                user.username = form.username.data
                user.email = form.email.data

                db.session.commit()
                flash('Profile updated!', 'success')
                return redirect(url_for('view_profile'))

            except IntegrityError:
                db.session.rollback()
                flash('That username is already taken!', 'warning')

        form.password.errors.append('Wrong password, please try again.')

    return render_template('/user/edit.html', user=g.user, form=form)

@app.route('/profile/edit-password', methods=['GET', 'POST'])
@auth_required
def edit_password():
    """Edit a user's password."""

    form = ChangePasswordForm(obj=g.user)

    if form.validate():
        if User.changePassword(g.user, form.current_password.data, form.new_password.data):
            db.session.commit()

            flash('Password updated!', 'success')
            return redirect(url_for('view_profile'))

        form.current_password.errors.append('Wrong current password, please try again.')

    return render_template('/user/edit_password.html', form=form)

@app.route('/profile/edit-location', methods=['GET', 'POST'])
@auth_required
def edit_location():
    """Edit a user's geolocation."""

    form = EditLocationForm()

    if form.validate_on_submit():
        user_location = UserLocation(city=form.city.data, state=form.state.data, country=form.country.data)
        coordinates = user_location.get_coordinates()

        if coordinates:
            g.user.latitude = coordinates['lat']
            g.user.longitude=coordinates['lng']

            db.session.commit()
            flash('Geolocation is updated.', 'success')
            return redirect(url_for('view_profile'))

        flash('There was an error fetching your geolocation. Please check the spelling of your City or State/Country and try again.', 'warning')

    return render_template('/user/edit_location.html', form=form)

@app.route('/profile/delete', methods=['POST'])
@auth_required
def delete_profile():
    """Delete a user's account and all data."""
    #Try to delete the user, if there is a problem tell the user why.
    try:
        #first we have to delete all plants
        user_plants = Plant.query.filter_by(user_id=g.user.id).all()
        for plant in user_plants:
            db.session.delete(plant)
            db.session.commit()

        #try to delete the user
        db.session.delete(g.user)
        db.session.commit()

        #delete user's uploads folder & files
        shutil.rmtree(f'{UPLOAD_FOLDER}/{g.user.id}')

        #delete user session
        if CURRENT_USER_KEY in session:
            del session[CURRENT_USER_KEY]
        
        flash('Account Deleted.', 'info')
        return redirect(url_for('homepage'))

    except IntegrityError:
        flash('There was a problem deleting your account.', 'warning')
        return redirect(url_for('dashboard'))

####################
# Collection Routes
####################

@app.route('/collections')
@auth_required
def show_collections():
    """Show user collection landing page."""

    collections = g.user.collections

    return render_template('/collection/view_collections.html', collections=collections)

@app.route('/collections/<int:collection_id>')
@auth_required
def view_collection(collection_id):
    """View a collection by id and all of the rooms inside the collection."""

    collection = Collection.query.get_or_404(collection_id)
    rooms = collection.rooms

    if collection.user_id != g.user.id:
        flash('Access Denied.', 'danger')
        return redirect(url_for('show_collections'))

    return render_template('/collection/view_collection.html', collection=collection, rooms=rooms)

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

    return render_template('/room/view_room.html', room=room, plants=plants, lightsources=lightsources)

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

    return render_template('/room/add_room.html', form=form, collection_id=collection_id)

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
            db.session.rollback()
            flash('You cannot delete a room that has plants!', 'warning')
            return redirect(url_for('view_room', room_id=room_id))
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
            db.session.rollback()
            flash('You cannot delete a lightsource that has plants using it! Change your plant lightsource first.', 'warning')
        return redirect(url_for('view_room', room_id=room.id))
    else:
        flash('Access Denied.', 'danger')
        return redirect(url_for('view_collection', collection_id=collection.id))

####################
# Plant Routes
####################

@app.route('/collection/room/plant/<int:plant_id>')
@auth_required
def view_plant(plant_id):
    """View a plants details by plant id. From the plant view you can
    edit plant details, view other details, or delete a plant."""

    plant = Plant.query.get_or_404(plant_id)
    water_schedule = WaterSchedule.query.filter_by(plant_id=plant_id).first()

    if g.user.id == plant.user_id:
        return render_template('/plant/view_plant.html', plant=plant, water_schedule=water_schedule)
    else:
        collection_id = plant.room.collection_id
        flash('Access Denied.', 'danger')
        return redirect(url_for('view_collection', collection_id=collection_id))

@app.route('/uploads/user/<path:filename>')
def download_file(filename):
    """Downloads the image from the respective user upload folder."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/collection/rooms/<int:room_id>/add-plant', methods=['GET', 'POST'])
@auth_required
def add_plant(room_id):
    """Add a new plant to a room by room id."""

    form = AddPlantForm()
    room = Room.query.get_or_404(room_id)
    collection = Collection.query.get_or_404(room.collection_id)
    #set the light_source query for the form
    form.light_source.query = LightSource.query.filter_by(room_id=room.id).all()

    if g.user.id == collection.user_id:
        if form.validate_on_submit():
            img = form.image.data
            #securely validate image (if included)
            if img:
                filename = secure_filename(img.filename)
                img.save(os.path.join(f'{UPLOAD_FOLDER}/{g.user.id}', filename))

                new_plant = Plant(
                    name=form.name.data,
                    image = f'{g.user.id}/{filename}',
                    user_id=g.user.id,
                    type_id=form.plant_type.data.id,
                    room_id=room.id,
                    light_id=form.light_source.data.id)
            else:
                new_plant = Plant(
                    name=form.name.data,
                    image=img,
                    user_id=g.user.id,
                    type_id=form.plant_type.data.id,
                    room_id=room.id,
                    light_id=form.light_source.data.id)

            room.plants.append(new_plant)
            db.session.commit()

            create_waterschedule(new_plant)
            flash(f'New plant, {new_plant.name}, added to {room.name}!', 'success')
            return redirect(url_for('view_room', room_id=room.id))
    else:
        flash('Access Denied.', 'danger')
        return redirect(url_for('view_collection', collection_id=collection.id))

    return render_template('/plant/add_plant.html', form=form, room=room)

@app.route('/collection/room/plant/<int:plant_id>/edit', methods=['GET', 'POST'])
@auth_required
def edit_plant(plant_id):
    """Edit a plant by id."""

    plant = Plant.query.get_or_404(plant_id)
    form = EditPlantForm(obj=plant)
    room = Room.query.get_or_404(plant.room_id)
    collection = Collection.query.get_or_404(room.collection_id)
    #set the light_source query for the form
    form.light_source.query = LightSource.query.filter_by(room_id=room.id).all()

    if g.user.id == plant.user_id:
        if form.validate_on_submit():
            #securely validate image (if included)
            img = form.image.data
            if img != plant.image:
                print(form.image)
                filename = secure_filename(img.filename)
                img.save(os.path.join(f'{UPLOAD_FOLDER}/{g.user.id}', filename))
                plant.image = f'{g.user.id}/{filename}'
            
            plant.name = form.name.data
            plant.type_id = form.plant_type.data.id
            plant.light_id = form.light_source.data.id
            db.session.commit()

            #reset the plant's water_schedule to reflect any changes in type or location but do not change the last water date.
            water_schedule = WaterSchedule.query.get_or_404(plant.id)
            plant_type = PlantType.query.get_or_404(plant.type_id)
            water_schedule.water_interval = plant_type.base_water
            water_schedule.next_water_date = water_schedule.water_date + timedelta(days=plant_type.base_water)
            db.session.commit()

            flash(f'{plant.name} updated!', 'success')
            return redirect(url_for('view_plant', plant_id=plant.id))
    else:
        flash('Access Denied.', 'danger')
        return redirect(url_for('view_collection', collection_id=collection.id))

    return render_template('/plant/edit_plant.html', form=form, plant=plant, room=room)

@app.route('/collection/room/plant/<int:plant_id>/delete', methods=['POST'])
@auth_required
def delete_plant(plant_id):
    """Delete a plant by id."""

    plant = Plant.query.get_or_404(plant_id)
    room = Room.query.get_or_404(plant.room_id)
    collection = Collection.query.get_or_404(room.collection_id)

    if g.user.id == plant.user_id:
        db.session.delete(plant)
        db.session.commit()
        return redirect(url_for('view_room', room_id=room.id))
    else:
        flash('Access Denied.', 'danger')
        return redirect(url_for('view_collection', collection_id=collection.id))

####################
# Schedule Routes
####################

def create_waterschedule(plant):
    """This is a helper method to create a Water Schedule for a newly added plant.
    Accepts a plant ORM object, sets water_date to current datetime and water interval
    is set from plant type base interval."""

    plant_type = PlantType.query.get_or_404(plant.type_id)

    plant.water_schedule.append(WaterSchedule(
        water_date=datetime.today(),
        next_water_date=datetime.today() + timedelta(days=plant_type.base_water),
        water_interval=plant_type.base_water,
        plant_id=plant.id
    ))
    db.session.commit()

@app.route('/water-manager')
@auth_required
def water_manager():
    """Task manager for watering all plants. Plants with next_water_date less than or equal to the current date will
    appear here to water or snooze."""

    form = AddWaterHistoryNotes(meta={'csrf': False})

    plants = Plant.query.filter_by(user_id=g.user.id).all()
    schedules = WaterSchedule.query.filter(WaterSchedule.next_water_date <= datetime.today()).all()
    plant_ids = [schedule.plant_id for schedule in schedules]
    plants_to_water = [plant for plant in plants if plant.id in plant_ids]

    return render_template('water_manager.html', user=g.user, plants=plants_to_water, form=form, schedules=schedules)

@app.route('/dashboard')
@auth_required
def dashboard():
    """Show the user dashboard for a specific user. Shows all Collections, Rooms, LightSources and Plants."""

    user = g.user
    collections = Collection.query.filter_by(user_id=g.user.id).all()

    return render_template('/dashboard.html', user=user, collections=collections)

@app.route('/water-manager/<int:plant_id>/water', methods=['POST'])
@auth_required
def water_plant(plant_id):
    """Waters a plant by plant id, updates the plant water schedule and updates the plant water history table."""

    plant = Plant.query.get_or_404(plant_id)
    water_schedule = WaterSchedule.query.get_or_404(plant.id)

    if g.user.id == plant.user_id:
        if water_schedule.manual_mode == True:

            water_schedule.water_date = datetime.today()
            water_schedule.next_water_date = datetime.today() + timedelta(days=water_schedule.water_interval)

            water_schedule.water_history.append(WaterHistory(
                water_date=water_schedule.water_date,
                notes=request.json['notes'],
                plant_id=plant.id,
                water_schedule_id=water_schedule.id
            ))

            db.session.commit()
            return (jsonify({"status": "OK"}), 201)
        else:
            plant_light_source = LightSource.query.get_or_404(plant.light_id)
            plant_type = PlantType.query.get_or_404(plant.type_id)

            #if light source is artifical, just update the next water date and add the history record.
            if plant_light_source.type == 'Artificial':
                water_schedule.next_water_date = datetime.today() + timedelta(days=water_schedule.water_interval)

                water_schedule.water_history.append(WaterHistory(
                    water_date=datetime.today(),
                    notes=request.json['notes'],
                    plant_id=plant.id,
                    water_schedule_id=water_schedule.id))

                db.session.commit()
                return (jsonify({"status": "OK"}), 201)

            #if the light source is natural, we need to calculate the next_water_date using the solar calculator light forcast and water calculator water internal.
            try:
                water_calculator = WaterCalculator(
                    user=g.user,
                    plant_type=plant_type,
                    water_schedule=water_schedule,
                    light_type=plant_light_source.type)
                    
                new_water_interval = water_calculator.calculate_water_interval()

                water_schedule.water_interval = new_water_interval
                water_schedule.water_date = datetime.today()
                water_schedule.next_water_date = datetime.today() + timedelta(days=new_water_interval)
                
                water_schedule.water_history.append(WaterHistory(
                    water_date=water_schedule.water_date,
                    notes=request.json['notes'],
                    plant_id=plant.id,
                    water_schedule_id=water_schedule.id))

                db.session.commit()
                return (jsonify({"status": "OK"}), 201)

            except ConnectionRefusedError:
                (jsonify({"connection": "REFUSED"}), 404)

    return (jsonify({"access": "DENIED"}), 403)

@app.route('/water-manager/<int:plant_id>/snooze', methods=['POST'])
@auth_required
def snooze_plant(plant_id,):
    """Snoozes a plant's water schedule for num of days, for a specific plant id.
    Updates the plant's water schedule and water history table indicating the plant was snoozed."""

    plant = Plant.query.get_or_404(plant_id)

    if g.user.id == plant.user_id:
        #update the water schedule and water history table
        water_schedule = WaterSchedule.query.get_or_404(plant.id)
        num_days = 3
        water_schedule.next_water_date = datetime.today() + timedelta(days=num_days)

        water_schedule.water_history.append(WaterHistory(
            water_date=water_schedule.water_date,
            snooze=num_days,
            notes=request.json['notes'],
            plant_id=plant.id,
            water_schedule_id=water_schedule.id
        ))

        db.session.commit()
        return (jsonify({"status": "OK"}), 201)

    return (jsonify({"access": "DENIED"}), 403)

@app.route('/collection/room/plant/<int:plant_id>/water-schedule/edit', methods=['GET', 'POST'])
@auth_required
def edit_waterschedule(plant_id):
    """Edit a plant's water schedule by plant id. 
    Editing a water schedule will toggle the plant's water schedule 
    between manual mode or auto. If the schedule is set to manual 
    intervals it will not adjust for seasonal changes."""

    plant = Plant.query.get_or_404(plant_id)
    room = Room.query.get_or_404(plant.room_id)
    collection = Collection.query.get_or_404(room.collection_id)
    water_schedule = WaterSchedule.query.filter_by(plant_id=plant_id).first()

    form = EditWaterScheduleForm(obj=water_schedule)

    if g.user.id == collection.user_id:
        if form.validate_on_submit():
            water_schedule.manual_mode = form.manual_mode.data
            water_schedule.water_interval = int(form.water_interval.data)
            water_schedule.next_water_date = water_schedule.water_date + timedelta(days=water_schedule.water_interval)
            db.session.commit()
            flash('Water Schedule updated.', 'success')
            return redirect(url_for('view_plant', plant_id=plant_id))
    else:
        flash('Access Denied.', 'danger')
        return redirect(url_for('view_plant', plant_id=plant_id))
    
    return render_template('/schedule/edit_waterschedule.html', form=form, water_schedule=water_schedule, plant=plant)

@app.route('/collection/room/plant/<int:plant_id>/water-history')
@auth_required
def view_waterhistory(plant_id):
    """View the water history table for a plant via the plant's id."""

    plant = Plant.query.get_or_404(plant_id)
    water_schedule = WaterSchedule.query.filter_by(plant_id=plant.id).first()
    water_history = WaterHistory.query.filter_by(water_schedule_id=water_schedule.id)

    if g.user.id == plant.user_id:
        return render_template('/schedule/view_waterhistory.html', plant=plant, water_history=water_history)
    
    flash('Access Denied.', 'danger')
    return redirect(url_for('view_plant', plant_id=plant_id)) 