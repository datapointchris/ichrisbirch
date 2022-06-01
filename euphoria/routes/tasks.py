import base64
import calendar
import random
from collections import Counter
from datetime import date, datetime, time, timedelta
from io import BytesIO
from zoneinfo import ZoneInfo

import requests
from flask import Blueprint, current_app, redirect, render_template, request, url_for
from matplotlib.figure import Figure

from ..database.sqlalchemy import session
from ..easy_dates import EasyDateTime
from ..models.tasks import Task, calculate_average_completion_time

blueprint = Blueprint(
    'tasks',
    __name__,
    template_folder='templates/tasks',
    static_folder='static',
)


@blueprint.route('/', methods=['GET'])
def priority():
    today = datetime.combine(date.today(), time())
    tomorrow = today + timedelta(days=1)
    with session:
        completed_today = (
            session.query(Task)
            .where(Task.complete_date > today, Task.complete_date < tomorrow)
            .all()
        )
        top_tasks = (
            session.query(Task)
            .where(Task.complete_date.is_(None))
            .order_by(Task.priority.asc(), Task.add_date.asc())
            .limit(5 - len(completed_today))
            .all()
        )
    return render_template(
        'tasks/priority.html', top_tasks=top_tasks, completed_today=completed_today
    )


@blueprint.route('/all')
def tasks():
    with session:
        tasks = (
            session.query(Task)
            .where(Task.complete_date.is_(None))
            .order_by(Task.priority.asc(), Task.add_date.asc())
            .all()
        )
    return render_template('tasks/all.html', tasks=tasks)


@blueprint.route('/completed/', methods=['GET', 'POST'])
def completed():
    with session:
        q = session.query(Task).where(Task.complete_date.is_not(None))
        first_completed_task = q.order_by(Task.complete_date.asc()).first()
        last_completed_task = q.order_by(Task.complete_date.desc()).first()

    ed = EasyDateTime()
    filters = {
        'today': (ed.today, ed.tomorrow),
        'yesterday': (ed.yesterday, ed.today),
        'this_week': (ed.week_start, ed.week_end),
        'last_7': (ed.previous_7, ed.today),
        'this_month': (ed.this_month, ed.next_month),
        'last_30': (ed.previous_30, ed.today),
        'this_year': (ed.this_year, ed.next_year),
        'all': (first_completed_task.complete_date, last_completed_task.complete_date),
    }

    if request.method == 'POST':
        date_filter = request.form.get('filter')
    else:
        date_filter = 'this_week'

    start_date, end_date = filters.get(date_filter)
    with session:
        completed_tasks = (
            session.query(Task)
            .where(
                Task.complete_date >= start_date,
                Task.complete_date < end_date,
            )
            .order_by(Task.complete_date.desc())
            .all()
        )

    average_completion = calculate_average_completion_time(completed_tasks)

    # Graph
    # TODO: Update this to something better for graphing
    # This is quick and dirty for now
    timestamps_for_filter = {
        dt: 0
        for dt in [start_date + timedelta(days=x) for x in range((end_date - start_date).days)]
    }
    completed_task_timestamps = Counter(
        [
            datetime(task.complete_date.year, task.complete_date.month, task.complete_date.day)
            for task in completed_tasks
        ]
    )
    all_dates_with_counts = {**timestamps_for_filter, **completed_task_timestamps}
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
        'tasks/completed.html',
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


@blueprint.route('/form/', methods=['POST'])
def form():
    api_url = current_app.config.get('API_URL')
    data = request.form.to_dict()
    method = data.pop('method')
    match method:
        case ['add']:
            task = Task(**data)
            response = requests.post(f'{api_url}/tasks', data=task)
        case ['complete']:
            task_id = data.get('id')
            response = requests.post(f'{api_url}/tasks/{task_id}/complete')
        case ['delete']:
            task_id = data.get('id')
            response = requests.delete(f'{api_url}/tasks/{task_id}')

    return redirect(url_for('tasks.index'))


@blueprint.route('/fake/', methods=['GET'])
def fake_tasks():
    with session:
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
            session.add(Task(**task))
        session.commit()
    return redirect(url_for('tasks.priority'))


@blueprint.route('/drop/', methods=['GET'])
def drop_tasks():
    with session:
        # session.execute(delete(Task))
        session.delete(Task)
        session.commit()
    return redirect(url_for('tasks.priority'))
