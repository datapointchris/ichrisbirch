import logging
from collections import Counter
from datetime import datetime
from datetime import timedelta
from typing import Any

import httpx
import pydantic
from fastapi import status
from flask import Blueprint
from flask import Response
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from ichrisbirch import schemas
from ichrisbirch.app.easy_dates import EasyDateTime
from ichrisbirch.app.helpers import handle_if_not_response_code
from ichrisbirch.app.helpers import url_builder
from ichrisbirch.config import get_settings

settings = get_settings()
blueprint = Blueprint('habits', __name__, template_folder='templates/habits', static_folder='static')

logger = logging.getLogger(__name__)

HABITS_API_URL = url_builder(settings.api_url, 'habits')


def create_completed_habit_chart_data(habits: list[schemas.HabitCompleted]) -> tuple[list[str], list[int]]:
    """Create chart labels and values from completed habits for chart.js"""

    # Ex: Friday, January 01, 2001
    DATE_FORMAT = '%A, %B %d, %Y'

    first = habits[0]
    last = habits[-1]

    all_timestamps_for_range = [
        first.complete_date + timedelta(days=x) for x in range((last.complete_date - first.complete_date).days)
    ]
    timestamps_zero_counts = {timestamp: 0 for timestamp in all_timestamps_for_range}
    completed_counts = Counter(
        [datetime(habit.complete_date.year, habit.complete_date.month, habit.complete_date.day) for habit in habits]
    )
    all_dates_with_counts = timestamps_zero_counts | completed_counts
    # Reversed for chronological display in chart.js
    chart_labels = [datetime.strftime(dt, DATE_FORMAT) for dt in reversed(all_dates_with_counts)]
    chart_values = list(reversed(list(all_dates_with_counts.values())))
    return chart_labels, chart_values


@blueprint.route('/', methods=['GET', 'POST'])
def index():

    edt = EasyDateTime()
    start_date, end_date = edt.filters.get('today', (None, None))
    params = {'start_date': str(start_date), 'end_date': str(end_date)}

    completed_response = httpx.get(url_builder(HABITS_API_URL, 'completed'), params=params)
    handle_if_not_response_code(200, completed_response, logger)
    completed = [schemas.HabitCompleted(**habit) for habit in completed_response.json()]
    completed_names = [habit.name for habit in completed]

    daily_response = httpx.get(HABITS_API_URL)
    handle_if_not_response_code(200, daily_response, logger)
    daily = [schemas.Habit(**habit) for habit in daily_response.json()]
    # TODO: [2024/04/27] - Find better way to filter these out
    daily_filtered = [habit for habit in daily if habit.name in completed_names]

    return render_template(
        'habits/index.html',
        completed=completed,
        habits=daily_filtered,
        long_date=edt.today.strftime('%A %B %d, %Y'),
    )


@blueprint.route('/completed/', methods=['GET', 'POST'])
def completed():
    """Completed habits"""
    DEFAULT_DATE_FILTER = 'this_week'
    edt = EasyDateTime()
    selected_filter = request.form.get('filter', '') if request.method == 'POST' else DEFAULT_DATE_FILTER
    start_date, end_date = edt.filters.get(selected_filter, (None, None))
    logger.debug(f'date filter: {selected_filter} = {start_date} - {end_date}')

    if start_date is None or end_date is None:
        params = {}
    else:
        params = {'start_date': str(start_date), 'end_date': str(end_date)}

    completed_response = httpx.get(url_builder(HABITS_API_URL, 'completed'), params=params)
    handle_if_not_response_code(200, completed_response, logger)
    completed_habits = [schemas.HabitCompleted(**habit) for habit in completed_response.json()]
    if completed_habits:
        completed_count = len(completed_habits)
        chart_labels, chart_values = create_completed_habit_chart_data(completed_habits)
    else:
        completed_count = f"No completed habits for time period: {' '.join(selected_filter.split('_')).capitalize()}"
        chart_labels, chart_values = None, None

    daily_response = httpx.get(HABITS_API_URL)
    handle_if_not_response_code(200, daily_response, logger)
    daily = [schemas.Habit(**habit) for habit in daily_response.json()]

    return render_template(
        'habits/completed.html',
        habits=daily,
        completed=completed_habits,
        completed_count=completed_count,
        filters=list(edt.filters) + ['all'],  # additional 'all' filter to frontend
        date_filter=selected_filter,
        chart_labels=chart_labels,
        chart_values=chart_values,
        zip=zip,
        long_date=edt.today.strftime('%A %B %d, %Y'),
    )


@blueprint.route('/manage/', methods=['GET'])
def manage():

    current_habits_response = httpx.get(HABITS_API_URL)
    handle_if_not_response_code(200, current_habits_response, logger)
    current_habits = [schemas.Habit(**habit) for habit in current_habits_response.json()]

    current_categories_response = httpx.get(url_builder(HABITS_API_URL, 'categories'))
    handle_if_not_response_code(200, current_categories_response, logger)
    current_categories = [schemas.HabitCategory(**habit) for habit in current_categories_response.json()]

    completed_response = httpx.get(url_builder(HABITS_API_URL, 'completed'))
    handle_if_not_response_code(200, completed_response, logger)
    completed_habits = [schemas.HabitCompleted(**habit) for habit in completed_response.json()]

    return render_template(
        'habits/manage.html',
        current_habits=current_habits,
        current_categories=current_categories,
        completed_habits=completed_habits,
    )


@blueprint.route('/crud/', methods=['POST'])
def crud():
    data: dict[str, Any] = request.form.to_dict()
    action = data.pop('action')
    logger.debug(f'{request.referrer=} {action=}')
    logger.debug(f'{data=}')

    if action == 'add_habit':
        try:
            category = schemas.HabitCreate(**data)
        except pydantic.ValidationError as e:
            logger.exception(e)
            flash(str(e), 'error')
            return redirect(request.referrer or url_for('habits.manage'))
        response = httpx.post(HABITS_API_URL, content=category.model_dump_json())
        handle_if_not_response_code(201, response, logger)
        return redirect(request.referrer or url_for('habits.manage'))

    elif action == 'complete_habit':
        url = url_builder(HABITS_API_URL, 'complete', data.get('id'))
        response = httpx.post(url)
        handle_if_not_response_code(200, response, logger)
        return redirect(request.referrer or url_for('habits.manage'))

    elif action == 'delete_habit':
        url = url_builder(HABITS_API_URL, data.get('id'))
        response = httpx.delete(url)
        handle_if_not_response_code(204, response, logger)
        return redirect(request.referrer or url_for('habits.manage'))

    elif action == 'add_category':
        try:
            category = schemas.HabitCategoryCreate(**data)
        except pydantic.ValidationError as e:
            logger.exception(e)
            flash(str(e), 'error')
            return redirect(request.referrer or url_for('habits.manage'))
        response = httpx.post(url_builder(HABITS_API_URL, 'categories'), content=category.model_dump_json())
        handle_if_not_response_code(201, response, logger)
        return redirect(request.referrer or url_for('habits.manage'))

    elif action == 'delete_category':
        url = url_builder(HABITS_API_URL, 'categories', data.get('id'))
        response = httpx.delete(url)
        handle_if_not_response_code(204, response, logger)
        return redirect(request.referrer or url_for('habits.manage'))

    return Response(f'Method/Action {action} not accepted', status=status.HTTP_405_METHOD_NOT_ALLOWED)
