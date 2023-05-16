from flask import Blueprint, render_template

from ichrisbirch.config import get_settings

settings = get_settings()

blueprint = Blueprint(
    'home',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/')
def index():
    """Website homepage"""
    return render_template('index.html', settings=settings)
