from flask import Blueprint, redirect, render_template, request, url_for


home_bp = Blueprint(
    'home_bp',
    __name__,
    template_folder='templates', static_folder='static'
)


@home_bp.route('/', methods=['GET'])
def home():
    return render_template('home.html')
