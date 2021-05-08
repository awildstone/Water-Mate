"""A file to seed the database with tables and LightType and PlantType data."""

from csv import DictReader
from app import db
from models import LightType, PlantType

#create the tables
db.create_all()

#now seed the DB with our shared data
artificial = LightType(type='Artificial')
north = LightType(type='North')
east = LightType(type='East')
south = LightType(type='South')
west = LightType(type='West')
northeast = LightType(type='Northeast')
northwest = LightType(type='Northwest')
southeast = LightType(type='Southeast')
southwest = LightType(type='Southwest')

db.session.add_all([artificial, north, east, south, west, northeast, northwest, southeast, southwest])
db.session.commit()

with open('generator/plant_types.csv') as plant_types:
    db.session.bulk_insert_mappings(PlantType, DictReader(plant_types))

db.session.commit()