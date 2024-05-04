from flask import Blueprint
from flask import render_template

blueprint = Blueprint(
    'portfolio',
    __name__,
    template_folder='templates/portfolio',
    static_folder='static',
)


@blueprint.route('/')
def index():
    """Portfolio home endpoint."""
    return render_template('index.html')
