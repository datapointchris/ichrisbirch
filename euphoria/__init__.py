from flask import Flask

from euphoria.apartments.db_manager import ApartmentsDBManager
from euphoria.moving.db_manager import BoxDBManager

# from database import database

### DATABASES ###
# TODO: These need to have the same DB format, probably a base class or protocol!!!!
# Make them take the same connection maybe even.  Just grab the tables for each connection


apt_db = ApartmentsDBManager('apartments.db')
# db.execute_sql_file(url_for('static', filename='sql/create_tables.sql'))

box_db = BoxDBManager('moving.db')
# with open('box_packing/static/sql/create_db.sql', 'r') as f:
#             db.run_sql_script(f)

# Blueprints
from euphoria.home.routes import home_bp
from euphoria.cockpit.routes import cockpit_bp
from euphoria.portfolio.routes import portfolio_bp
from euphoria.apartments.routes import apartments_bp
from euphoria.moving.routes import moving_bp


def create_app():
    app = Flask(__name__)
    # setup with the configuration provided
    # app.config.from_object('config.DevelopmentConfig')

    # setup all our dependencies
    # database.init_app(app)
    with app.app_context():
        app.register_blueprint(home_bp)
        app.register_blueprint(cockpit_bp, url_prefix='/cockpit')
        app.register_blueprint(portfolio_bp, url_prefix='/portfolio')
        app.register_blueprint(apartments_bp, url_prefix='/apartments')
        app.register_blueprint(moving_bp, url_prefix='/moving')

        return app
