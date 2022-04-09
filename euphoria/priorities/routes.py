import base64
import calendar
from dataclasses import dataclass
import random
from collections import Counter
from datetime import date, datetime, time, timedelta
from io import BytesIO

from euphoria import db
from euphoria.priorities.helpers import calculate_average_completion_time
from euphoria.priorities.models import Task
from flask import Blueprint, redirect, render_template, request, url_for
from matplotlib.figure import Figure
from sqlalchemy import delete, select

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


@priorities_bp.route('/fake/', methods=['GET'])
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
    return redirect(url_for('priorities_bp.priority'))


@priorities_bp.route('/drop/', methods=['GET'])
def drop_tasks():
    db.session.execute(delete(Task))
    db.session.commit()
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
    db.session.execute(delete(Task).where(Task.id == request.form.get('id')))
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


@priorities_bp.route('/completed/', methods=['GET', 'POST'])
def completed():
    first_completed_task = (
        db.session.execute(
            select(Task)
            .where(Task.complete_date.is_not(None))
            .order_by(Task.complete_date.asc())
        )
        .scalars()
        .first()
    )
    # Easy to read dates
    start_of_time = first_completed_task.complete_date.replace(tzinfo=None)
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

    @dataclass
    class Filter:
        query_filter: tuple
        start: datetime
        end: datetime

        @property
        def filter_datetimes(self) -> datetime:
            return [
                self.start + timedelta(days=x)
                for x in range((self.end - self.start).days)
            ]

    filters = {
        'all': Filter(
            (Task.complete_date > start_of_time, Task.complete_date < tomorrow),
            start_of_time,
            tomorrow,
        ),
        'today': Filter(
            (Task.complete_date > today, Task.complete_date < tomorrow),
            today,
            tomorrow,
        ),
        'yesterday': Filter(
            (Task.complete_date > yesterday, Task.complete_date < today),
            yesterday,
            today,
        ),
        'this_week': Filter(
            (Task.complete_date > week_start, Task.complete_date < week_end),
            week_start,
            week_end,
        ),
        'last_7': Filter(
            (Task.complete_date > previous_7, Task.complete_date < today),
            previous_7,
            today,
        ),
        'this_month': Filter(
            (Task.complete_date > this_month, Task.complete_date < next_month),
            this_month,
            next_month,
        ),
        'last_30': Filter(
            (Task.complete_date > previous_30, Task.complete_date < today),
            previous_30,
            today,
        ),
        'this_year': Filter(
            (Task.complete_date > this_year, Task.complete_date < next_year),
            this_year,
            next_year,
        ),
    }
    if request.method == 'POST':
        selected_filter = request.form.get('filter')
    else:
        selected_filter = 'this_week'
    filter = filters.get(selected_filter, 'this_week')
    completed = (
        db.session.execute(
            select(Task).where(*filter.query_filter).order_by(Task.complete_date.desc())
        )
        .scalars()
        .all()
    )
    average_completion = calculate_average_completion_time(completed)

    all_dates = {dt: 0 for dt in filter.filter_datetimes}
    task_counts = Counter(
        datetime(
            task.complete_date.year, task.complete_date.month, task.complete_date.day
        )
        for task in reversed(completed)
    )
    all_dates_with_counts = {**all_dates, **task_counts}
    x = all_dates_with_counts.keys()
    y = all_dates_with_counts.values()
    x_labels = [datetime.strftime(dt, '%m/%d') for dt in all_dates_with_counts]
    fig = Figure(figsize=(16, 6))
    ax = fig.subplots()
    ax.set_xticklabels(labels=x_labels)
    ax.bar(x, y)
    buffer = BytesIO()
    fig.savefig(buffer, format="png")
    image_data = base64.b64encode(buffer.getbuffer()).decode("ascii")

    return render_template(
        'completed.html',
        completed=completed,
        average_completion=average_completion,
        filters=filters,
        selected_filter=selected_filter,
        image_data=image_data,
    )
