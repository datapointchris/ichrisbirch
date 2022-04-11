import base64
import calendar
import random
from collections import Counter
from datetime import date, datetime, time, timedelta
from io import BytesIO

from euphoria import db
from euphoria.tasks.helpers import calculate_average_completion_time
from euphoria.tasks.models import Task
from flask import Blueprint, redirect, render_template, request, url_for
from matplotlib.figure import Figure
from sqlalchemy import delete, select

tasks_bp = Blueprint(
    'tasks_bp',
    __name__,
    template_folder='templates/tasks',
    static_folder='static',
)


@tasks_bp.route('/')
def tasks():
    tasks = (
        Task.query.filter(Task.complete_date.is_(None))
        .order_by(Task.priority.asc(), Task.add_date.asc())
        .all()
    )
    return render_template('tasks.html', tasks=tasks)


@tasks_bp.route('/priority/', methods=['GET'])
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
    top_tasks = (
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
        'priority.html', top_tasks=top_tasks, completed_today=completed_today
    )


@tasks_bp.route('/completed/', methods=['GET', 'POST'])
def completed():
    # Easy to use dates for filters
    today = datetime.combine(date.today(), time())
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)
    previous_7 = today - timedelta(days=7)
    previous_30 = today - timedelta(days=30)
    _month_days = calendar.monthrange(today.year, today.month)[1]
    week_number = today.isocalendar().week
    week_start = datetime.combine(
        date.fromisocalendar(today.year, week_number, 1), time()
    )
    week_end = week_start + timedelta(days=7)
    this_month = datetime(today.year, today.month, 1)
    next_month = this_month + timedelta(days=_month_days)
    this_year = datetime(today.year, 1, 1)
    next_year = datetime(today.year + 1, 1, 1)

    first_completed_task = (
        db.session.execute(
            select(Task)
            .where(Task.complete_date.is_not(None))
            .order_by(Task.complete_date.asc())
        )
        .scalars()
        .first()
    )
    last_completed_task = (
        db.session.execute(
            select(Task)
            .where(Task.complete_date.is_not(None))
            .order_by(Task.complete_date.desc())
        )
        .scalars()
        .first()
    )
    filters = {
        'today': (today, tomorrow),
        'yesterday': (yesterday, today),
        'this_week': (week_start, week_end),
        'last_7': (previous_7, today),
        'this_month': (this_month, next_month),
        'last_30': (previous_30, today),
        'this_year': (this_year, next_year),
        'all': (first_completed_task.complete_date, last_completed_task.complete_date),
    }

    if request.method == 'POST':
        selected_filter = request.form.get('filter')
    else:
        selected_filter = 'this_week'

    filter_start_date, filter_end_date = filters.get(selected_filter)
    completed_tasks = (
        db.session.execute(
            select(Task)
            .where(
                Task.complete_date >= filter_start_date,
                Task.complete_date < filter_end_date,
            )
            .order_by(Task.complete_date.desc())
        )
        .scalars()
        .all()
    )

    average_completion = calculate_average_completion_time(completed_tasks)

    # Graph
    tstamps = [
        filter_start_date + timedelta(days=x)
        for x in range((filter_end_date - filter_start_date).days)
    ]
    all_dates = {dt: 0 for dt in tstamps}
    task_complete_dates = [
        datetime(
            task.complete_date.year, task.complete_date.month, task.complete_date.day
        )
        for task in completed_tasks
    ]
    task_counts = Counter(task_complete_dates)
    all_dates_with_counts = {**all_dates, **task_counts}
    x = all_dates_with_counts.keys()
    y = all_dates_with_counts.values()
    x_labels = [datetime.strftime(dt, '%m/%d') for dt in all_dates_with_counts]
    fig = Figure(figsize=(16, 6))
    ax = fig.subplots()
    ax.bar(x, y)
    ax.set_xticklabels(labels=x_labels)
    buffer = BytesIO()
    fig.savefig(buffer, format="png")
    image_data = base64.b64encode(buffer.getbuffer()).decode("ascii")

    return render_template(
        'completed.html',
        completed_tasks=completed_tasks,
        average_completion=average_completion,
        filters=filters,
        selected_filter=selected_filter,
        image_data=image_data,
    )

# TODO: When the API is working, use those endpoints instead of these

@tasks_bp.route('/add/', methods=['POST'])
def add_task():
    db.session.add(Task(**request.form))
    db.session.commit()
    return redirect(url_for('tasks_bp.priority'))


@tasks_bp.route('/complete/', methods=['POST'])
def complete_task():
    task = Task.query.filter_by(id=request.form.get('id')).first()
    task.complete_date = datetime.now()
    db.session.commit()
    return redirect(url_for('tasks_bp.priority'))


@tasks_bp.route('/delete/', methods=['POST'])
def delete_task():
    db.session.execute(delete(Task).where(Task.id == request.form.get('id')))
    db.session.commit()
    return redirect(url_for('tasks_bp.priority'))


@tasks_bp.route('/fake/', methods=['GET'])
def fake_tasks():
    for _ in range(100):
        tstamp = datetime.utcnow() - timedelta(days=random.randint(0, 100))
        completed = (
            tstamp + timedelta(days=random.randint(0, 100)),
            None,
            None,
            None,
        )
        task = {
            'name': f'task {round(random.random() * 100, 2)}',
            'category': random.choice(['financial', 'coding', 'chore', 'car', 'misc']),
            'subcategory1': None,
            'subcategory2': None,
            'priority': random.randint(0, 100),
            'add_date': tstamp,
            'complete_date': random.choice(completed),
        }
        db.session.add(Task(**task))
    db.session.commit()
    return redirect(url_for('tasks_bp.priority'))


@tasks_bp.route('/drop/', methods=['GET'])
def drop_tasks():
    db.session.execute(delete(Task))
    db.session.commit()
    return redirect(url_for('tasks_bp.priority'))
