"""Flask App for Water Mate."""

from flask import Flask, render_template, request, flash, redirect, session, g, url_for
from sqlalchemy.exc import IntegrityError
from functools import wraps
from models import db, connect_db, #import the Models created
# from forms import #import the forms created

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (os.environ.get('DATABASE_URL', 'postgres:///water_mate'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'J28r$CC&Z5NCN48O$CEe&749k')
#Disables Flask file caching
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

connect_db(app)