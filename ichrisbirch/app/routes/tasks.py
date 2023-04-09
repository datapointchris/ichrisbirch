import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

import requests
from flask import Blueprint, abort, redirect, render_template, request, url_for

from ichrisbirch import schemas
from ichrisbirch.app.easy_dates import EasyDateTime
from ichrisbirch.config import settings
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
TIMEOUT = settings.REQUEST_TIMEOUT


def get_first_and_last_task():
    first = requests.get(f'{TASKS_URL}/completed/', params={'first': True}, timeout=TIMEOUT).json()
    last = requests.get(f'{TASKS_URL}/completed/', params={'last': True}, timeout=TIMEOUT).json()
    first_task = schemas.TaskCompleted(**first)
    last_task = schemas.TaskCompleted(**last)
    return first_task, last_task


def days_to_complete(task: schemas.Task) -> int | None:
    """Calculate days it took to complete task"""
    if task.complete_date:
        return max((task.complete_date - task.add_date).days, 1)
    return None


def calculate_average_completion_time(tasks: list[schemas.TaskCompleted]) -> str:
    """ "Calculate the average completion time of the supplied completed tasks"""
    if not tasks:
        return 'No tasks completed for this time period'
    total_days_to_complete = sum([max((task.complete_date - task.add_date).days, 1) for task in tasks])
    average_days = total_days_to_complete / len(tasks)
    weeks, days = divmod(average_days, 7)
    return f'{int(weeks)} weeks, {int(days)} days'


@blueprint.route('/', methods=['GET'])
def index():
    """Tasks home endpoint"""
    ed = EasyDateTime()
    top_tasks_json = requests.get(TASKS_URL, params={'limit': 5}, timeout=TIMEOUT).json()
    top_tasks = [schemas.Task(**task) for task in top_tasks_json]

    today_filter = {'start_date': str(ed.today), 'end_date': str(ed.tomorrow)}
    completed_tasks_json = requests.get(f'{TASKS_URL}/completed/', params=today_filter, timeout=TIMEOUT).json()
    completed_today = [schemas.TaskCompleted(**task) for task in completed_tasks_json]

    return render_template(
        'tasks/index.html',
        top_tasks=top_tasks,
        completed_today=completed_today,
        task_categories=TASK_CATEGORIES,
    )


@blueprint.route('/all/')
def all():
    """All tasks endpoint"""
    all_tasks_json = requests.get(f'{settings.API_URL}/tasks/', timeout=TIMEOUT).json()
    all_tasks = [schemas.Task(**task) for task in all_tasks_json]
    return render_template('tasks/all.html', tasks=all_tasks, task_categories=TASK_CATEGORIES)


@blueprint.route('/completed/', methods=['GET', 'POST'])
def completed():
    """Completed tasks endpoint.  Filtered by date selection."""
    DEFAULT_DATE_FILTER = 'this_week'
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

    if request.method == 'POST':
        date_filter = request.form.get('filter')
        if not date_filter:
            logger.warning('"filter" parameter expected for POST')
            date_filter = DEFAULT_DATE_FILTER
    else:
        date_filter = DEFAULT_DATE_FILTER

    start_date, end_date = date_filters.get(date_filter, (None, None))
    logger.debug(f'Date filter: {date_filter} = {start_date} - {end_date}')

    tasks_filter = {'start_date': start_date, 'end_date': end_date}

    completed_tasks_json = requests.get(f'{TASKS_URL}/completed/', params=tasks_filter, timeout=TIMEOUT).json()
    completed_tasks = [schemas.TaskCompleted(**task) for task in completed_tasks_json]
    if completed_tasks:
        first = completed_tasks[0]
        last = completed_tasks[-1]
        average_completion = calculate_average_completion_time(completed_tasks)

        filter_timestamps = [
            first.complete_date + timedelta(days=x) for x in range((last.complete_date - first.complete_date).days)
        ]
        timestamps_for_filter = {timestamp: 0 for timestamp in filter_timestamps}
        completed_task_timestamps = Counter(
            [
                datetime(task.complete_date.year, task.complete_date.month, task.complete_date.day)
                for task in completed_tasks
            ]
        )
        all_dates_with_counts = {**timestamps_for_filter, **completed_task_timestamps}
        chart_labels = [datetime.strftime(dt, '%m/%d') for dt in all_dates_with_counts]
        chart_values = all_dates_with_counts.values()
    else:
        average_completion = f"No completed tasks for this time period '{date_filter}'"
        chart_labels = None
        chart_values = None

    return render_template(
        'tasks/completed.html',
        completed_tasks=completed_tasks,
        average_completion=average_completion,
        filters=date_filters,
        date_filter=date_filter,
        chart_labels=chart_labels,
        chart_values=chart_values,
        task_categories=TASK_CATEGORIES,
        zip=zip,
    )


@blueprint.route('/crud/', methods=['POST'])
def crud():
    """CRUD endpoint for tasks"""
    data: dict[str, Any] = request.form.to_dict()
    method = data.pop('method')
    logger.debug(f'{method=}')
    logger.debug(data)
    match method:
        case 'add':
            task = schemas.TaskCreate(**data).json()
            response = requests.post(TASKS_URL, data=task, timeout=TIMEOUT)
            logger.debug(response.text)
            return redirect(url_for('tasks.index'))  # TODO: Redirect back to referring page
        case 'complete':
            task_id = data.get('id')
            response = requests.post(f'{TASKS_URL}/complete/{task_id}', timeout=TIMEOUT)
            logger.debug(response.text)
            return redirect(url_for('tasks.index'))
        case 'delete':
            task_id = data.get('id')
            response = requests.delete(f'{TASKS_URL}/{task_id}', timeout=TIMEOUT)
            logger.debug(response.text)
            return redirect(url_for('tasks.all'))
    return abort(405, description=f"Method {method} not accepted")
