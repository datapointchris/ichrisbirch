import base64
import calendar
import random
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from io import BytesIO
from zoneinfo import ZoneInfo

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


@tasks_bp.route('/all')
def tasks():
    tasks = (
        db.session.execute(
            select(Task)
            .where(Task.complete_date.is_(None))
            .order_by(Task.priority.asc(), Task.add_date.asc())
        )
        .scalars()
        .all()
    )
    return render_template('tasks.html', tasks=tasks)


@tasks_bp.route('/', methods=['GET'])
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
    return render_template('priority.html', top_tasks=top_tasks, completed_today=completed_today)


class Filter:
    def __init__(self):
        pass


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
    week_start = datetime.combine(date.fromisocalendar(today.year, week_number, 1), time())
    week_end = week_start + timedelta(days=7)
    this_month = datetime(today.year, today.month, 1)
    next_month = this_month + timedelta(days=_month_days)
    this_year = datetime(today.year, 1, 1)
    next_year = datetime(today.year + 1, 1, 1)

    # TODO: These need to become methods of the Task class
    # to call then is ??
    # Hmm where do these custom queries go?
    first_completed_task = (
        db.session.execute(
            select(Task).where(Task.complete_date.is_not(None)).order_by(Task.complete_date.asc())
        )
        .scalars()
        .first()
    )
    last_completed_task = (
        db.session.execute(
            select(Task).where(Task.complete_date.is_not(None)).order_by(Task.complete_date.desc())
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
        date_filter = request.form.get('filter')
    else:
        date_filter = 'this_week'

    date_filter_start, date_filter_end = filters.get(date_filter)
    completed_tasks = (
        db.session.execute(
            select(Task)
            .where(
                Task.complete_date >= date_filter_start,
                Task.complete_date < date_filter_end,
            )
            .order_by(Task.complete_date.desc())
        )
        .scalars()
        .all()
    )

    average_completion = calculate_average_completion_time(completed_tasks)

    # Graph
    filter_timestamps = {
        dt: 0
        for dt in [
            date_filter_start + timedelta(days=x)
            for x in range((date_filter_end - date_filter_start).days)
        ]
    }
    completed_task_timestamps = Counter(
        [
            datetime(task.complete_date.year, task.complete_date.month, task.complete_date.day)
            for task in completed_tasks
        ]
    )
    all_dates_with_counts = {**filter_timestamps, **completed_task_timestamps}
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
        date_filter=date_filter,
        image_data=image_data,
    )

# FIXME: When adding a task, the date is stuck at 4/21
# Most likely a problem when postgres started and the default value.
# I think the fix is that I need to set the default in SQLAlchemy
# and the db will be created with the proper default by Alembic
# Christ! whenever I get around to adding Alembic as well
@tasks_bp.route('/add/', methods=['POST'])
def add_task():
    db.session.add(Task(**request.form))
    db.session.commit()
    return redirect(url_for('tasks_bp.priority'))


@tasks_bp.route('/complete/', methods=['POST'])
def complete_task():
    task = Task.query.filter_by(id=request.form.get('id')).first()
    task.complete_date = datetime.now(tz=ZoneInfo("America/Chicago"))
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
        tstamp = datetime.now(tz=ZoneInfo("America/Chicago")) - timedelta(
            days=random.randint(0, 100)
        )
        task = {
            'name': f'task {round(random.random() * 100, 2)}',
            'category': random.choice(['financial', 'coding', 'chore', 'car', 'misc']),
            'priority': random.randint(0, 100),
            'add_date': tstamp.isoformat(),
            'complete_date': random.choices(
                [(tstamp + timedelta(days=random.randint(0, 100))).isoformat(), None],
                k=1,
                weights=[1, 3],
            ),
        }
        db.session.add(Task(**task))
    db.session.commit()
    return redirect(url_for('tasks_bp.priority'))


@tasks_bp.route('/drop/', methods=['GET'])
def drop_tasks():
    db.session.execute(delete(Task))
    db.session.commit()
    return redirect(url_for('tasks_bp.priority'))
