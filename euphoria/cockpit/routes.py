from flask import Blueprint, redirect, render_template, request, url_for
from flask import current_app as app


cockpit_bp = Blueprint(
    'cockpit_bp', __name__, template_folder='templates/cockpit', static_folder='static'
)


@cockpit_bp.route('/', methods=['GET'])
def cockpit():
    return render_template('index.html')
