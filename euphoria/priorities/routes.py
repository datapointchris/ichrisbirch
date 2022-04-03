from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for
from euphoria import priorities_db as db
import random
import sqlalchemy

from euphoria.priorities.models import Task

priorities_bp = Blueprint(
    'priorities_bp',
    __name__,
    template_folder='templates/priorities',
    static_folder='static',
)


def add_fake_tasks(number):
    completed = (datetime.utcnow(), None, None, None)
    for _ in range(number):
        task = {
            'name': f'task {random.random()}',
            'category': 'financial',
            'subcategory1': None,
            'subcategory2': None,
            'priority': random.randint(0, 100),
            'add_date': datetime.utcnow(),
            'complete_date': random.choice(completed),
        }
        db.session.add(Task(**task))
    db.session.commit()


@priorities_bp.route('/', methods=['GET'])
def toptasks():
    # add_fake_tasks(10)
    top_5_tasks = (
        Task.query.filter(Task.complete_date.is_(None))
        .order_by(Task.priority.asc(), Task.add_date.asc())
        .limit(5)
        .all()
    )
    # print(top_5_tasks)

    return render_template('toptasks.html', top_5_tasks=top_5_tasks)


@priorities_bp.route('/add/', methods=['POST'])
def add_task():
    db.session.add(Task(**request.form))
    db.session.commit()
    return redirect(url_for('priorities_bp.toptasks'))


@priorities_bp.route('/update/', methods=['POST'])
def update_task():
    task = Task.query.filter_by(id=request.form.get('id')).first()
    db.session.execute(sqlalchemy.update(Task).where(Task.id == task.id).values(**task))
    db.session.commit()
    return redirect(url_for('priorities_bp.toptasks'))


@priorities_bp.route('/delete/', methods=['POST'])
def delete_task():
    print('DELETE DELETE')
    print(request.form.get('id'))
    task = Task.query.filter_by(id=request.form.get('id')).first()
    print('TASK')
    print(task)
    db.session.execute(sqlalchemy.delete(Task).where(Task.id == task.id))
    db.session.commit()
    return redirect(url_for('priorities_bp.toptasks'))


@priorities_bp.route('/tasks/')
def all_tasks():
    tasks = (
        Task.query.filter(Task.complete_date.is_(None))
        .order_by(Task.priority.asc(), Task.add_date.asc())
        .all()
    )
    return render_template('all_tasks.html', tasks=tasks)
