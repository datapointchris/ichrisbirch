from flask import Blueprint, redirect, render_template, request, url_for
from flask import current_app as app


portfolio_bp = Blueprint(
    'portfolio_bp', __name__, template_folder='templates/portfolio', static_folder='static'
)


@portfolio_bp.route('/', methods=['GET'])
def portfolio():
    return render_template('index.html')
