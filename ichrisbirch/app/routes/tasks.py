import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

import requests
from flask import Blueprint, abort, redirect, render_template, request, url_for

from ichrisbirch import schemas
from ichrisbirch.app.easy_dates import EasyDateTime
from ichrisbirch.config import get_settings
from ichrisbirch.models.task import TaskCategory

settings = get_settings()
blueprint = Blueprint(
    'tasks',
    __name__,
    template_folder='templates/tasks',
    static_folder='static',
)

logger = logging.getLogger(__name__)

TASKS_URL = f'{settings.api_url}/tasks'
TASK_CATEGORIES = [t.value for t in TaskCategory]
TIMEOUT = settings.request_timeout


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


def calculate_average_completion_time(tasks: list[schemas.TaskCompleted]) -> str | None:
    """ "Calculate the average completion time of the supplied completed tasks"""
    if not tasks:
        return None
    total_days_to_complete = sum([max((task.complete_date - task.add_date).days, 1) for task in tasks])
    average_days = total_days_to_complete / len(tasks)
    weeks, days = divmod(average_days, 7)
    return f'{int(weeks)} weeks, {int(days)} days'


def create_completed_task_chart_data(tasks: list[schemas.TaskCompleted]) -> tuple[list[str], list[int]]:
    """Create chart labels and values from completed tasks"""
    first = tasks[0]
    last = tasks[-1]

    filter_timestamps = [
        first.complete_date + timedelta(days=x) for x in range((last.complete_date - first.complete_date).days)
    ]
    timestamps_for_filter = {timestamp: 0 for timestamp in filter_timestamps}
    completed_task_timestamps = Counter(
        [datetime(task.complete_date.year, task.complete_date.month, task.complete_date.day) for task in tasks]
    )
    all_dates_with_counts = {**timestamps_for_filter, **completed_task_timestamps}
    chart_labels = [datetime.strftime(dt, '%m/%d') for dt in all_dates_with_counts]
    chart_values = list(all_dates_with_counts.values())
    return chart_labels, chart_values


@blueprint.route('/', methods=['GET'])
def index():
    """Tasks home endpoint"""
    ed = EasyDateTime()
    params: dict[str, str | int] = {'completed_filter': 'not_completed', 'limit': 5}
    top_tasks_json = requests.get(TASKS_URL, params=params, timeout=TIMEOUT).json()
    print(f'{top_tasks_json=}')
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


@blueprint.route('/all/', methods=['GET', 'POST'])
def all():
    """All tasks endpoint"""

    completed_filter = request.form.get('completed_filter') if request.method == 'POST' else None
    params = {'completed_filter': completed_filter}
    print(f'{completed_filter=}')
    logger.debug(f'{completed_filter=}')

    tasks_json = requests.get(TASKS_URL, params=params, timeout=TIMEOUT).json()
    print(f'{tasks_json=}')
    tasks = [schemas.Task(**task) for task in tasks_json]
    return render_template(
        'tasks/all.html', tasks=tasks, task_categories=TASK_CATEGORIES, completed_filter=completed_filter
    )


@blueprint.route('/completed/', methods=['GET', 'POST'])
def completed():
    """Completed tasks endpoint.  Filtered by date selection."""
    DEFAULT_DATE_FILTER = 'this_week'
    edt = EasyDateTime()
    date_filters = edt.filters

    selected_filter = (
        request.form.get('filter', DEFAULT_DATE_FILTER) if request.method == 'POST' else DEFAULT_DATE_FILTER
    )

    start_date, end_date = date_filters.get(selected_filter, (None, None))
    logger.debug(f'Date filter: {selected_filter} = {start_date} - {end_date}')

    params = {'start_date': str(start_date), 'end_date': str(end_date)}

    completed_tasks_json = requests.get(f'{TASKS_URL}/completed/', params=params, timeout=TIMEOUT).json()
    completed_tasks = [schemas.TaskCompleted(**task) for task in completed_tasks_json]

    if completed_tasks:
        average_completion = calculate_average_completion_time(completed_tasks)
        chart_labels, chart_values = create_completed_task_chart_data(completed_tasks)
    else:
        average_completion = f"No completed tasks for this time period '{selected_filter}'"
        chart_labels, chart_values = None, None

    return render_template(
        'tasks/completed.html',
        completed_tasks=completed_tasks,
        average_completion=average_completion,
        filters=date_filters,
        date_filter=selected_filter,
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
    logger.debug(f'{request.referrer=}')
    logger.debug(f'{method=}')
    logger.debug(f'{data}')
    match method:
        case 'add':
            task = schemas.TaskCreate(**data).json()
            response = requests.post(TASKS_URL, data=task, timeout=TIMEOUT)
            logger.debug(response.text)
            return redirect(request.referrer or url_for('tasks.index'))
        case 'complete':
            task_id = data.get('id')
            response = requests.post(f'{TASKS_URL}/complete/{task_id}', timeout=TIMEOUT)
            logger.debug(response.text)
            return redirect(request.referrer or url_for('tasks.index'))
        case 'delete':
            task_id = data.get('id')
            response = requests.delete(f'{TASKS_URL}/{task_id}', timeout=TIMEOUT)
            logger.debug(response.text)
            return redirect(request.referrer or url_for('tasks.all'))
        case 'search':
            search_terms = data.get('terms')
            logger.debug(f'{search_terms=}')
            tasks_json = requests.get(f'{TASKS_URL}/search/{search_terms}', timeout=TIMEOUT).json()
            logger.debug(tasks_json)
            tasks = [schemas.Task(**task) for task in tasks_json]
            return render_template('tasks/search.html', tasks=tasks)
    return abort(405, description=f"Method {method} not accepted")
