import base64
import logging
import random
from collections import Counter
from datetime import datetime, timedelta
from io import BytesIO
from zoneinfo import ZoneInfo

import requests
from faker import Faker
from flask import Blueprint, redirect, render_template, request, url_for
from matplotlib.figure import Figure
from euphoria import settings

from euphoria.backend.app.easy_dates import EasyDateTime
from euphoria.backend.common import models, schemas
from euphoria.backend.common.db.sqlalchemy import session

blueprint = Blueprint(
    'tasks',
    __name__,
    template_folder='templates/tasks',
    static_folder='static',
)

logger = logging.getLogger(__name__)


@blueprint.route('/', methods=['GET'])
def index():
    ed = EasyDateTime()
    completed_today = requests.get(
        f'{settings.API_URL}/tasks/completed/',
        params={'start_date': ed.today, 'end_date': ed.tomorrow},
    ).json()
    top_tasks = requests.get(f'{settings.API_URL}/tasks/', params={'limit': 5}).json()
    completed_today = [models.Task(**schemas.Task(**task).dict()) for task in completed_today]
    top_tasks = [models.Task(**schemas.Task(**task).dict()) for task in top_tasks]
    return render_template('tasks/index.html', top_tasks=top_tasks, completed_today=completed_today)


@blueprint.route('/all')
def all():
    tasks = requests.get(f'{settings.API_URL}/tasks/').json()
    return render_template('tasks/all.html', tasks=tasks)


@blueprint.route('/completed/', methods=['GET', 'POST'])
def completed():
    ed = EasyDateTime()
    filters = {
        'today': (ed.today, ed.tomorrow),
        'yesterday': (ed.yesterday, ed.today),
        'this_week': (ed.week_start, ed.week_end),
        'last_7': (ed.previous_7, ed.tomorrow),
        'this_month': (ed.this_month, ed.next_month),
        'last_30': (ed.previous_30, ed.tomorrow),
        'this_year': (ed.this_year, ed.next_year),
        'all': (None, None),
    }
    date_filter = request.form.get('filter') if request.method == 'POST' else 'this_week'
    if date_filter == 'all':  # have to query db to get first and last
        first = requests.get(f'{settings.API_URL}/tasks/completed/', params={'first': True}).json()
        last = requests.get(f'{settings.API_URL}/tasks/completed/', params={'last': True}).json()
        start_date = schemas.Task(**first).complete_date
        end_date = schemas.Task(**last).complete_date + timedelta(seconds=1)
    else:
        start_date, end_date = filters.get(date_filter)
    logger.debug(f'Date filter: {date_filter} = {start_date} - {end_date}')
    print(f'Date filter: {date_filter} = {start_date} - {end_date}')

    completed_tasks = requests.get(
        f'{settings.API_URL}/tasks/completed/',
        params={'start_date': start_date, 'end_date': end_date},
    ).json()
    completed_tasks = [models.Task(**schemas.Task(**task).dict()) for task in completed_tasks]
    if completed_tasks:
        average_days = sum(task.days_to_complete for task in completed_tasks) / len(completed_tasks)
        weeks, days = divmod(average_days, 7)
        average_completion = f'{int(weeks)} weeks, {int(days)} days'
    else:
        average_completion = 'No tasks completed for this time period'

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


@blueprint.route('/form/', methods=['POST'])
def form():
    data = request.form.to_dict()
    method = data.pop('method')
    logger.debug(f'{method=}')
    logger.debug(data)
    match method:
        case 'add':
            task = schemas.TaskCreate(**data).json()
            response = requests.post(f'{settings.API_URL}/tasks/', data=task)
            logger.debug(response.text)
            return redirect(url_for('tasks.index'))  # TODO: Redirect back to referring page
        case 'complete':
            task_id = data.get('id')
            response = requests.post(f'{settings.API_URL}/tasks/complete/{task_id}')
            logger.debug(response.text)
            return redirect(url_for('tasks.index'))
        case 'delete':
            task_id = data.get('id')
            response = requests.delete(f'{settings.API_URL}/tasks/{task_id}')
            logger.debug(response.text)
            return redirect(url_for('tasks.all'))


@blueprint.route('/fake/', methods=['GET'])
def fake_tasks():
    fake = Faker()
    with session:
        for _ in range(1000):
            tstamp = datetime.now(tz=ZoneInfo("America/Chicago")) - timedelta(
                days=random.randint(0, 100)
            )
            task = {
                'name': fake.catch_phrase(),
                'category': random.choice(['financial', 'coding', 'chore', 'car', 'misc']),
                'priority': random.randint(1, 100),
                'add_date': tstamp.isoformat(),
                'complete_date': random.choices(
                    [(tstamp + timedelta(days=random.randint(0, 100))).isoformat(), None],
                    k=1,
                    weights=[1, 3],
                )[0],
            }
            session.add(models.Task(**task))
        session.commit()
    return redirect(url_for('tasks.index'))


@blueprint.route('/drop/', methods=['GET'])
def drop_tasks():
    with session:
        # session.execute(delete(Task))
        session.delete(models.Task)
        session.commit()
    return redirect(url_for('tasks.index'))
