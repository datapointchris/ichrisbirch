from flask import Blueprint, render_template
from euphoria import config

blueprint = Blueprint(
    'main',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/')
def index():
    return render_template('index.html', settings=config)
