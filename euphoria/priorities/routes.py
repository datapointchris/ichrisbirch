from datetime import datetime, timedelta, date, time
from flask import Blueprint, render_template, request, redirect, url_for
from euphoria import priorities_db as db
import random
from sqlalchemy import delete, select


from euphoria.priorities.models import Task
from euphoria.priorities.helpers import calculate_average_completion_time

priorities_bp = Blueprint(
    'priorities_bp',
    __name__,
    template_folder='templates/priorities',
    static_folder='static',
)


@priorities_bp.route('/', methods=['GET'])
def priority():
    today = datetime.combine(date.today(), time())
    tomorrow = today + timedelta(days=1)
    completed_today = (
        db.session.execute(
            select(Task).where(Task.complete_date > today, Task.complete_date < tomorrow)
        )
        .scalars()
        .all()
    )
    top_5_tasks = (
        db.session.execute(
            select(Task)
            .where(Task.complete_date.is_(None))
            .order_by(Task.priority.asc(), Task.add_date.asc())
            .limit(5 - len(completed_today))
        )
        .scalars()
        .all()
    )

    return render_template(
        'priority.html', top_5_tasks=top_5_tasks, completed_today=completed_today
    )


@priorities_bp.route('/fake/', methods=['GET'])
def fake_tasks():
    def add_fake_tasks(number):
        for _ in range(number):
            tstamp = datetime.utcnow() - timedelta(days=random.randint(0, 100))
            completed = (
                tstamp + timedelta(days=random.randint(0, 100)),
                None,
                None,
                None,
            )
            task = {
                'name': f'task {random.random()}',
                'category': 'financial',
                'subcategory1': None,
                'subcategory2': None,
                'priority': random.randint(0, 100),
                'add_date': tstamp,
                'complete_date': random.choice(completed),
            }
            db.session.add(Task(**task))
        db.session.commit()

    add_fake_tasks(100)
    return redirect(url_for('priorities_bp.priority'))


@priorities_bp.route('/add/', methods=['POST'])
def add_task():
    db.session.add(Task(**request.form))
    db.session.commit()
    return redirect(url_for('priorities_bp.priority'))


@priorities_bp.route('/complete/', methods=['POST'])
def complete_task():
    task = Task.query.filter_by(id=request.form.get('id')).first()
    task.complete_date = datetime.now()
    db.session.commit()
    return redirect(url_for('priorities_bp.priority'))


@priorities_bp.route('/delete/', methods=['POST'])
def delete_task():
    task = Task.query.filter_by(id=request.form.get('id')).first()
    db.session.execute(delete(Task).where(Task.id == task.id))
    db.session.commit()
    return redirect(url_for('priorities_bp.priority'))


@priorities_bp.route('/tasks/')
def tasks():
    tasks = (
        Task.query.filter(Task.complete_date.is_(None))
        .order_by(Task.priority.asc(), Task.add_date.asc())
        .all()
    )
    return render_template('tasks.html', tasks=tasks)


@priorities_bp.route('/completed/')
def completed():
    # TODO: Finish this with filters for display
    if request.method == 'POST':
        selected_filter = request.form.get('filter')
    filters = {
        'no_filter': Task.complete_date.is_not(None),
    }
    completed = (
        Task.query.filter(Task.complete_date.is_not(None))
        .order_by(Task.complete_date.desc())
        .all()
    )
    average_completion = calculate_average_completion_time(completed)
    return render_template(
        'completed.html', completed=completed, average_completion=average_completion
    )
