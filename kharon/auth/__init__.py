from flask import Blueprint

tunnistautuminen = Blueprint('auth', __name__)

from . import views
