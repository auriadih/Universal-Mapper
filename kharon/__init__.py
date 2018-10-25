# import Flask microframework and SQLAlchemy library for PostgreSQL connections
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# import user accounts library
from flask_login import LoginManager

# import session system
from flask import session

# import config from local file
#from config import app_config # global config file, in root folder (on same level as 'kontiainen' folder)

# import Bootstrap template library
from flask_bootstrap import Bootstrap



# db connection initialization
db = SQLAlchemy()
login_manager = LoginManager()



# define main application
def create_app():

	# initialize Flask app
    app = Flask(__name__, instance_relative_config=True)

    # fetch configuration
    #app.config.from_object(app_config[config_name])
    app.config['DEBUG'] = True
    app.config['SQLALCHEMY_ECHO'] = True # True
    app.config.from_pyfile('config.py') # read from 'instance/config.py'

    # initialize db
    db.init_app(app)

	# initialize login manager
    login_manager.init_app(app)
    login_manager.login_message = "Kirjaudu sisään nähdäksesi tämän sivun."
    login_manager.login_view = "auth.login"
    login_manager.session_protection = "strong"

    # initiate Bootstrap environment
    Bootstrap(app)

	# import user-defined local models for database queries
    from kharon import models

	# import auth blueprints from local files
    from .auth import tunnistautuminen as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .browser import browser as browser_blueprint
    app.register_blueprint(browser_blueprint)

    # output
    return app
