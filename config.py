import os
from dotenv import load_dotenv
#SECRET_KEY = os.urandom(32)
# Grabs the folder where the script runs.
basedir = os.path.abspath(os.path.dirname(__file__))


# Enable debug mode.
# Connect to the database
# TODO IMPLEMENT DATABASE URL


class Config:
    load_dotenv()
    password = os.environ['PASSWORD']
    SECRET_KEY = os.urandom(32)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = f'postgresql://postgres:{password}@localhost:5432/fyyur'
    SESSION_TYPE = "filesystem"
    SESSION_PERMANENT = False
    DEBUG = True