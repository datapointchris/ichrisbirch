import logging
from collections import Counter
from datetime import datetime, timedelta
from typing import Any

import httpx
import pendulum
import pydantic
from fastapi import status
from flask import Blueprint, Response, flash, redirect, render_template, request, url_for

from ichrisbirch import schemas
from ichrisbirch.app.easy_dates import EasyDateTime
from ichrisbirch.app.helpers import handle_if_not_response_code, url_builder
from ichrisbirch.config import get_settings
from ichrisbirch.models.task import TaskCategory

settings = get_settings()
blueprint = Blueprint('tasks', __name__, template_folder='templates/tasks', static_folder='static')

logger = logging.getLogger(__name__)

TASKS_API_URL = f'{settings.api_url}/tasks/'
TASK_CATEGORIES = [t.value for t in TaskCategory]


def get_first_and_last_task():
    url = url_builder(TASKS_API_URL, 'completed')
    first = httpx.get(url, params={'first': True}).json()
    last = httpx.get(url, params={'last': True}).json()
    first_task = schemas.TaskCompleted(**first)
    last_task = schemas.TaskCompleted(**last)
    return first_task, last_task


def calculate_average_completion_time(tasks: list[schemas.TaskCompleted]) -> str | None:
    """Calculate the average completion time of the supplied completed tasks"""
    average_days = sum(task.days_to_complete for task in tasks) / len(tasks)
    weeks, days = divmod(average_days, 7)
    return f'{int(weeks)} weeks, {int(days)} days'


def create_completed_task_chart_data(tasks: list[schemas.TaskCompleted]) -> tuple[list[str], list[int]]:
    """Create chart labels and values from completed tasks for chart.js"""

    # Ex: Friday, January 01, 2001
    DATE_FORMAT = '%A, %B %d, %Y'

    first = tasks[0]
    last = tasks[-1]

    filter_timestamps = [
        first.complete_date + timedelta(days=x) for x in range((last.complete_date - first.complete_date).days)
    ]
    timestamps_for_filter = {timestamp: 0 for timestamp in filter_timestamps}
    completed_task_timestamps = Counter(
        [datetime(task.complete_date.year, task.complete_date.month, task.complete_date.day) for task in tasks]
    )
    all_dates_with_counts = timestamps_for_filter | completed_task_timestamps
    # Reversed for chronological display in chart.js
    chart_labels = [datetime.strftime(dt, DATE_FORMAT) for dt in reversed(all_dates_with_counts)]
    chart_values = list(reversed(list(all_dates_with_counts.values())))
    return chart_labels, chart_values


def critical_tasks_count(tasks: list[schemas.Task]) -> int:
    return sum(1 for task in tasks if task.priority <= 1)


def warning_tasks_count(tasks: list[schemas.Task]) -> int:
    return sum(1 for task in tasks if task.priority > 1 and task.priority <= 3)


def query_tasks_with_error_handling(
    endpoint: str = '',
    params: dict = {},
    expected_response_code: int = 200,
) -> list[schemas.Task]:
    response = httpx.get(url_builder(TASKS_API_URL, endpoint), params=params)
    handle_if_not_response_code(expected_response_code, response, logger)
    return [schemas.Task(**task) for task in response.json()]


def query_completed_tasks_with_error_handling(
    endpoint: str = 'completed',
    params: dict = {},
    expected_response_code: int = 200,
) -> list[schemas.TaskCompleted]:
    response = httpx.get(url_builder(TASKS_API_URL, endpoint), params=params)
    handle_if_not_response_code(expected_response_code, response, logger)
    return [schemas.TaskCompleted(**task) for task in response.json()]


@blueprint.route('/', methods=['GET'])
def index():
    tasks = query_tasks_with_error_handling('todo')
    critical_count = critical_tasks_count(tasks)
    warning_count = warning_tasks_count(tasks)

    completed_today_params = {'start_date': str(pendulum.today()), 'end_date': str(pendulum.tomorrow())}
    completed_today = query_completed_tasks_with_error_handling(params=completed_today_params)

    return render_template(
        'tasks/index.html',
        top_tasks=tasks[:5],
        critical_count=critical_count,
        warning_count=warning_count,
        completed_today=completed_today,
        task_categories=TASK_CATEGORIES,
    )


@blueprint.route('/todo/', methods=['GET', 'POST'])
def todo():
    tasks = query_tasks_with_error_handling('todo')
    critical_count = critical_tasks_count(tasks)
    warning_count = warning_tasks_count(tasks)
    return render_template(
        'tasks/todo.html',
        tasks=tasks,
        critical_count=critical_count,
        warning_count=warning_count,
        todo_count=len(tasks),
        task_categories=TASK_CATEGORIES,
    )


@blueprint.route('/completed/', methods=['GET', 'POST'])
def completed():
    """Completed tasks endpoint.  Filtered by date selection."""
    DEFAULT_DATE_FILTER = 'this_week'
    edt = EasyDateTime()
    selected_filter = request.form.get('filter', '') if request.method == 'POST' else DEFAULT_DATE_FILTER
    start_date, end_date = edt.filters.get(selected_filter, (None, None))
    logger.debug(f'date filter: {selected_filter} = {start_date} - {end_date}')

    if start_date is None or end_date is None:
        params = {}
    else:
        params = {'start_date': str(start_date), 'end_date': str(end_date)}

    if completed_tasks := query_completed_tasks_with_error_handling(params=params):
        average_completion = calculate_average_completion_time(completed_tasks)
        chart_labels, chart_values = create_completed_task_chart_data(completed_tasks)
    else:
        average_completion = f"No completed tasks for time period: {' '.join(selected_filter.split('_')).capitalize()}"
        chart_labels, chart_values = None, None

    return render_template(
        'tasks/completed.html',
        completed_tasks=completed_tasks,
        average_completion=average_completion,
        filters=list(edt.filters) + ['all'], # additional 'all' filter to frontend
        date_filter=selected_filter,
        chart_labels=chart_labels,
        chart_values=chart_values,
        task_categories=TASK_CATEGORIES,
        zip=zip,
    )


@blueprint.route('/search/', methods=['GET', 'POST'])
def search():
    if request.method == 'GET':
        todo_tasks, completed_tasks = [], []
    else:
        data: dict[str, Any] = request.form.to_dict()
        search_terms = data.get('terms')
        logger.debug(f'{request.referrer=} | {search_terms=}')

        if not search_terms:
            flash('No search terms provided', 'warning')
            return render_template('tasks/search.html', tasks=[])

        tasks = query_tasks_with_error_handling('search', params={'q': search_terms})
        todo_tasks = [task for task in tasks if not task.complete_date]
        completed_tasks = [schemas.TaskCompleted(**task.model_dump()) for task in tasks if task.complete_date]

    return render_template(
        'tasks/search.html', todo_tasks=todo_tasks, completed_tasks=completed_tasks, task_categories=TASK_CATEGORIES
    )


@blueprint.route('/add/', methods=['GET', 'POST'])
def add():
    return render_template('tasks/add.html', task_categories=TASK_CATEGORIES)


@blueprint.route('/crud/', methods=['POST'])
def crud():
    data: dict[str, Any] = request.form.to_dict()
    action = data.pop('action')
    logger.debug(f'{request.referrer=} {action=}')
    logger.debug(f'{data=}')

    if action == 'add':
        try:
            task = schemas.TaskCreate(**data)
        except pydantic.ValidationError as e:
            logger.exception(e)
            flash(str(e), 'error')
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        response = httpx.post(TASKS_API_URL, content=task.model_dump_json())
        handle_if_not_response_code(201, response, logger)
        return redirect(request.referrer or url_for('tasks.index'))

    elif action == 'complete':
        url = url_builder(TASKS_API_URL, 'complete', data.get('id'))
        response = httpx.post(url)
        handle_if_not_response_code(200, response, logger)
        return redirect(request.referrer or url_for('tasks.index'))

    elif action == 'delete':
        url = url_builder(TASKS_API_URL, data.get('id'))
        response = httpx.delete(url)
        handle_if_not_response_code(204, response, logger)
        return redirect(request.referrer or url_for('tasks.todo'))

    elif action == 'extend7':
        url = url_builder(TASKS_API_URL, data.get('id'))
        response = httpx.patch(url, params={'extension': 7})
        handle_if_not_response_code(200, response, logger)
        return redirect(request.referrer or url_for('tasks.todo'))

    elif action == 'extend30':
        url = url_builder(TASKS_API_URL, data.get('id'))
        response = httpx.patch(url, params={'extension': 30})
        handle_if_not_response_code(200, response, logger)
        return redirect(request.referrer or url_for('tasks.todo'))

    return Response(f'Method/Action {action} not accepted', status=status.HTTP_405_METHOD_NOT_ALLOWED)
