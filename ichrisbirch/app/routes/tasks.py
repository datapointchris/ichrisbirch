import logging
from collections import Counter
from datetime import datetime
from datetime import timedelta

import pendulum
from fastapi import status
from flask import Blueprint
from flask import Response
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_login import login_required

from ichrisbirch import schemas
from ichrisbirch.app import forms
from ichrisbirch.app.easy_dates import EasyDateTime
from ichrisbirch.app.query_api import QueryAPI
from ichrisbirch.config import settings
from ichrisbirch.models.task import TaskCategory

logger = logging.getLogger('app.tasks')
blueprint = Blueprint('tasks', __name__, template_folder='templates/tasks', static_folder='static')


# Ex: Friday, January 01, 2001
DATE_FORMAT = '%A, %B %d, %Y'
TZ = settings.global_timezone
TASK_CATEGORIES = [t.value for t in TaskCategory]


@blueprint.before_request
@login_required
def enforce_login():
    pass


@blueprint.context_processor
def inject_task_create_form():
    """Create a task create form for the request context.

    Since the add task form is on every page, this will inject the create form into the context.
    `before_request` is not the correct decorator to use
    """
    create_form = forms.TaskCreateForm()
    return dict(create_form=create_form)


def calculate_average_completion_time(tasks: list[schemas.TaskCompleted]) -> str | None:
    """Calculate the average completion time of the supplied completed tasks."""
    average_days = sum(task.days_to_complete for task in tasks) / len(tasks)
    weeks, days = divmod(average_days, 7)
    return f'{int(weeks)} weeks, {int(days)} days'


def create_completed_task_chart_data(tasks: list[schemas.TaskCompleted]) -> tuple[list[str], list[int]]:
    """Create chart labels and values from completed tasks for chart.js."""
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


def due_soon_tasks(tasks: list[schemas.Task]) -> int:
    return sum(1 for task in tasks if 2 < task.priority <= 5)


def critical_tasks(tasks: list[schemas.Task]) -> int:
    return sum(1 for task in tasks if 0 < task.priority <= 2)


def overdue_tasks(tasks: list[schemas.Task]) -> int:
    return sum(1 for task in tasks if task.priority < 1)


@blueprint.route('/', methods=['GET'])
def index():
    tasks_api = QueryAPI(base_url='tasks', logger=logger, response_model=schemas.Task)
    tasks_completed_api = QueryAPI(base_url='tasks/completed', logger=logger, response_model=schemas.TaskCompleted)
    tasks = tasks_api.get_many('todo')
    critical_count = critical_tasks(tasks)
    due_soon_count = due_soon_tasks(tasks)
    overdue_count = overdue_tasks(tasks)

    completed_today_params = {'start_date': str(pendulum.today(TZ)), 'end_date': str(pendulum.tomorrow(TZ))}
    completed_today = tasks_completed_api.get_many(params=completed_today_params)

    return render_template(
        'tasks/index.html',
        top_tasks=tasks[:5],
        critical_count=critical_count,
        due_soon_count=due_soon_count,
        overdue_count=overdue_count,
        total_count=len(tasks),
        completed_today=completed_today,
        task_categories=TASK_CATEGORIES,
    )


@blueprint.route('/todo/', methods=['GET', 'POST'])
def todo():
    tasks_api = QueryAPI(base_url='tasks', logger=logger, response_model=schemas.Task)
    tasks = tasks_api.get_many('todo')
    critical_count = critical_tasks(tasks)
    due_soon_count = due_soon_tasks(tasks)
    overdue_count = overdue_tasks(tasks)
    return render_template(
        'tasks/todo.html',
        tasks=tasks,
        critical_count=critical_count,
        due_soon_count=due_soon_count,
        overdue_count=overdue_count,
        total_count=len(tasks),
        task_categories=TASK_CATEGORIES,
    )


@blueprint.route('/completed/', methods=['GET', 'POST'])
def completed():
    """Completed tasks endpoint.

    Filtered by date selection.
    """
    tasks_completed_api = QueryAPI(base_url='tasks/completed', logger=logger, response_model=schemas.TaskCompleted)
    DEFAULT_DATE_FILTER = 'this_week'
    edt = EasyDateTime(tz=TZ)
    selected_filter = request.form.get('filter', '') if request.method == 'POST' else DEFAULT_DATE_FILTER
    start_date, end_date = edt.filters.get(selected_filter, (None, None))
    logger.debug(f'date filter: {selected_filter} = {start_date} - {end_date}')

    if start_date is None or end_date is None:
        params = {}
    else:
        params = {'start_date': str(start_date), 'end_date': str(end_date)}

    if completed_tasks := tasks_completed_api.get_many(params=params):
        average_completion = calculate_average_completion_time(completed_tasks)
        chart_labels, chart_values = create_completed_task_chart_data(completed_tasks)
    else:
        average_completion = f"No completed tasks for time period: {' '.join(selected_filter.split('_')).capitalize()}"
        chart_labels, chart_values = None, None

    return render_template(
        'tasks/completed.html',
        completed_tasks=completed_tasks,
        average_completion=average_completion,
        filters=list(edt.filters) + ['all'],  # additional 'all' filter to frontend
        date_filter=selected_filter,
        chart_labels=chart_labels,
        chart_values=chart_values,
        task_categories=TASK_CATEGORIES,
        total_completed=len(completed_tasks),
        zip=zip,
    )


@blueprint.route('/search/', methods=['GET', 'POST'])
def search():
    tasks_api = QueryAPI(base_url='tasks', logger=logger, response_model=schemas.Task)
    if request.method == 'GET':
        todo_tasks, completed_tasks = [], []
    else:
        data = request.form.to_dict()
        search_terms = data.get('terms')
        logger.debug(f'{request.referrer=}, {search_terms=}')

        if not search_terms:
            flash('No search terms provided', 'warning')
            return render_template('tasks/search.html', tasks=[])

        tasks = tasks_api.get_many('search', params={'q': search_terms})
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
    tasks_api = QueryAPI(base_url='tasks', logger=logger, response_model=schemas.Task)

    data = request.form.to_dict()
    action = data.pop('action')

    match action:
        case 'add':
            tasks_api.post(json=data)
            return redirect(request.referrer or url_for('tasks.index'))
        case 'complete':
            tasks_api.patch([data.get('id'), 'complete'])
            return redirect(request.referrer or url_for('tasks.index'))
        case 'extend':
            tasks_api.patch([data.get('id'), 'extend', data.get('days')])
            return redirect(request.referrer or url_for('tasks.todo'))
        case 'delete':
            tasks_api.delete(data.get('id'))
            return redirect(request.referrer or url_for('tasks.todo'))
        case 'reset_priorities':
            response = tasks_api.post_action('reset-priorities')
            message = response.json().get('message')
            flash(message, 'success')
            return redirect(request.referrer or url_for('tasks.todo'))

    return Response(f'Method/Action {action} not accepted', status=status.HTTP_405_METHOD_NOT_ALLOWED)
