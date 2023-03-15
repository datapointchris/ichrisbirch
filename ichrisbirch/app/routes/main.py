from flask import Blueprint, render_template

from ichrisbirch import config

blueprint = Blueprint(
    'main',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/')
def index():
    """Website main homepage"""
    return render_template('index.html', settings=config)
