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

from ichrisbirch import models, schemas
from ichrisbirch.app.easy_dates import EasyDateTime
from ichrisbirch.config import settings
from ichrisbirch.db.sqlalchemy import session
from ichrisbirch.models.tasks import TaskCategory

blueprint = Blueprint(
    'tasks',
    __name__,
    template_folder='templates/tasks',
    static_folder='static',
)

logger = logging.getLogger(__name__)

TASKS_URL = f'{settings.API_URL}/tasks'
TASK_CATEGORIES = [t.value for t in TaskCategory]


def validate_json_tasks(tasks: list[dict] | dict) -> list[models.Task]:
    """Validates returned JSON with Pydantic schema and SQLAlchemy Model"""
    validated = [schemas.Task(**task) for task in tasks]
    return [models.Task(**(task.dict())) for task in validated]


def calculate_average_completion(tasks: list[models.Task]) -> str:
    """ "Calculate the average completion time of the supplied completed tasks"""
    if not tasks:
        return 'No tasks completed for this time period'
    total_days = sum(task.days_to_complete for task in tasks)
    average_days = total_days / len(tasks)
    weeks, days = divmod(average_days, 7)
    return f'{int(weeks)} weeks, {int(days)} days'


@blueprint.route('/', methods=['GET'])
def index():
    """Tasks home endpoint"""
    ed = EasyDateTime()
    today_filter = {'start_date': ed.today, 'end_date': ed.tomorrow}

    top_tasks_json = requests.get(TASKS_URL, params={'limit': 5}, timeout=settings.REQUEST_TIMEOUT).json()
    top_tasks = validate_json_tasks(top_tasks_json)

    completed_tasks_json = requests.get(
        f'{TASKS_URL}/completed/', params=today_filter, timeout=settings.REQUEST_TIMEOUT
    ).json()
    completed_today = validate_json_tasks(completed_tasks_json)

    return render_template(
        'tasks/index.html',
        top_tasks=top_tasks,
        completed_today=completed_today,
        task_categories=TASK_CATEGORIES,
    )


@blueprint.route('/all')
def all():
    """All tasks endpoint"""
    all_tasks_json = requests.get(f'{settings.API_URL}/tasks/', timeout=settings.REQUEST_TIMEOUT).json()
    all_tasks = validate_json_tasks(all_tasks_json)
    return render_template('tasks/all.html', tasks=all_tasks, task_categories=TASK_CATEGORIES)


@blueprint.route('/completed/', methods=['GET', 'POST'])
def completed():
    """Completed tasks endpoint.  Filtered by date selection."""
    ed = EasyDateTime()
    date_filters = {
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
        first = requests.get(f'{TASKS_URL}/completed/', params={'first': True}, timeout=settings.REQUEST_TIMEOUT).json()
        last = requests.get(f'{TASKS_URL}/completed/', params={'last': True}, timeout=settings.REQUEST_TIMEOUT).json()
        start_date = schemas.Task(**first).complete_date
        end_date = schemas.Task(**last).complete_date + timedelta(seconds=1)
    else:
        start_date, end_date = date_filters.get(date_filter)
    logger.debug(f'Date filter: {date_filter} = {start_date} - {end_date}')

    tasks_filter = {'start_date': start_date, 'end_date': end_date}
    completed_tasks_json = requests.get(
        f'{TASKS_URL}/completed/',
        params=tasks_filter,
        timeout=settings.REQUEST_TIMEOUT,
    ).json()
    completed_tasks = validate_json_tasks(completed_tasks_json)
    average_completion = calculate_average_completion(completed_tasks)

    # Graph
    # TODO: Update this to something better for graphing
    # This is quick and dirty for now
    timestamps_for_filter = {
        dt: 0 for dt in [start_date + timedelta(days=x) for x in range((end_date - start_date).days)]
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
        filters=date_filters,
        date_filter=date_filter,
        image_data=image_data,
        task_categories=TASK_CATEGORIES,
    )


# TODO: [2023/02/10] - change form to crud
@blueprint.route('/form/', methods=['POST'])
def form():
    """CRUD endpoint for tasks"""
    data = request.form.to_dict()
    method = data.pop('method')
    logger.debug(f'{method=}')
    logger.debug(data)
    match method:
        case 'add':
            task = schemas.TaskCreate(**data).json()
            response = requests.post(TASKS_URL, data=task, timeout=settings.REQUEST_TIMEOUT)
            logger.debug(response.text)
            return redirect(url_for('tasks.index'))  # TODO: Redirect back to referring page
        case 'complete':
            task_id = data.get('id')
            response = requests.post(f'{TASKS_URL}/complete/{task_id}', timeout=settings.REQUEST_TIMEOUT)
            logger.debug(response.text)
            return redirect(url_for('tasks.index'))
        case 'delete':
            task_id = data.get('id')
            response = requests.delete(f'{TASKS_URL}/{task_id}', timeout=settings.REQUEST_TIMEOUT)
            logger.debug(response.text)
            return redirect(url_for('tasks.all'))


@blueprint.route('/fake/', methods=['GET'])
def fake_tasks():
    """Endpoint to create fake tasks for testing.
    NOTE: Not currently being used.
    """
    fake = Faker()
    with session:
        for _ in range(1000):
            tstamp = datetime.now(tz=ZoneInfo("America/Chicago")) - timedelta(days=random.randint(0, 100))
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
    """Endpoint for dropping all tasks from table.
    NOTE: Not currently being used, as it is scary.
    """
    with session:
        # session.execute(delete(Task))
        session.delete(models.Task)
        session.commit()
    return redirect(url_for('tasks.index'))
