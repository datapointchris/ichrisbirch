from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from euphoria import priorities_db

from euphoria.priorities.models import Task

priorities_bp = Blueprint(
    'priorities_bp',
    __name__,
    template_folder='templates/priorities',
    static_folder='static',
)


@priorities_bp.route('/', methods=['GET'])
def priorities():
    top_5_tasks = Task.query.all()
    print(top_5_tasks)

    return render_template('toptasks.html', top_5_tasks=top_5_tasks)
