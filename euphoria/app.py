from flask import Flask
from .routes import main, box_packing, countdowns, events, journal, habits


def create_app():
    app = Flask(__name__)

    with app.app_context():
        app.register_blueprint(main.blueprint)
        app.register_blueprint(box_packing.blueprint, url_prefix='/box-packing')
        app.register_blueprint(countdowns.blueprint, url_prefix='/countdowns')
        app.register_blueprint(events.blueprint, url_prefix='/events')
        app.register_blueprint(journal.blueprint, url_prefix='/journal')
        app.register_blueprint(habits.blueprint, url_prefix='/habits')

    return app
