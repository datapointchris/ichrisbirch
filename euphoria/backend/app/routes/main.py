from flask import Blueprint, render_template
from euphoria.backend.common import config

blueprint = Blueprint(
    'main',
    __name__,
    template_folder='templates',
    static_folder='static',
)


@blueprint.route('/')
def index():
    print('RENDER INDEX')
    return render_template('index.html', settings=config)
