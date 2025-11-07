from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from dotenv import load_dotenv
import os

load_dotenv()

db = SQLAlchemy()
app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET_KEY", "dev")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///musics.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# 🔥 esta linha é ESSENCIAL
migrate = Migrate(app, db)

from .models import User, Genero, Artista, Musica, UserGenero, UserArtista

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

from .views import *
