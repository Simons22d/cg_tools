from os.path import isfile
from flask import Flask, request, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
import random
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from dotenv import load_dotenv
import os
from flask_mail import Mail

load_dotenv()

db_user = os.getenv("DBUSER")
db_pass = os.getenv("DBPASS")

# __init__ the app
app = Flask(__name__)
ma = Marshmallow(app)
cors = CORS(app)

# setting sql_alchemy database consts
app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+mysqlconnector://root:@localhost:3306/tools"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = random.getrandbits(512)
app.config["MAIL_SERVER"] = "mail.cargen.com"
app.config["MAIL_PORT"] = 4050
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USERNAME"] = "itsupport@cargen.com"
app.config["MAIL_PASSWORD"] = 'support2020'

# adding marshmallow
db = SQLAlchemy(app)
migrate = Migrate(app, db)
mail = Mail(app)

from tools.routes.routes import *

CORS(app)
