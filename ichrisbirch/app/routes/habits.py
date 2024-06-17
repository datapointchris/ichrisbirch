import logging
from collections import Counter
from datetime import datetime
from datetime import timedelta
from typing import Any

import pendulum
from fastapi import status
from flask import Blueprint
from flask import Response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for

from ichrisbirch import schemas
from ichrisbirch.app.easy_dates import EasyDateTime
from ichrisbirch.app.query_api import QueryAPI
from ichrisbirch.config import get_settings

settings = get_settings()
logger = logging.getLogger('app.habits')
blueprint = Blueprint('habits', __name__, template_folder='templates/habits', static_folder='static')
habits_api = QueryAPI(base_url='habits', logger=logger, response_model=schemas.Habit)
habits_completed_api = QueryAPI(base_url='habits/completed', logger=logger, response_model=schemas.HabitCompleted)
habits_categories_api = QueryAPI(base_url='habits/categories', logger=logger, response_model=schemas.HabitCategory)
# Ex: Friday, January 01, 2001 12:00:00 EDT
DATE_FORMAT = '%A, %B %d, %Y %H:%M:%S %Z'
TZ = settings.global_timezone


def create_completed_habit_chart_data(habits: list[schemas.HabitCompleted]) -> tuple[list[str], list[int]]:
    """Create chart labels and values from completed habits for chart.js."""

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


def sort_habits_by_category(habits: list[schemas.Habit] | list[schemas.HabitCompleted]) -> dict[str, list]:
    categories = [habit.category.name for habit in habits]
    i = 'IMPORTANT'
    if i in categories:
        categories.remove(i)
        categories.insert(0, i)
    habits_by_category: dict[str, list] = {category: [] for category in categories}
    for habit in habits:
        habits_by_category[habit.category.name].append(habit)
    return habits_by_category


@blueprint.route('/', methods=['GET', 'POST'])
def index():

    params = {'start_date': str(pendulum.today(TZ)), 'end_date': str(pendulum.tomorrow(TZ))}
    completed = habits_completed_api.get_many(params=params)
    completed_by_category = sort_habits_by_category(completed)

    daily_habits = habits_api.get_many(params={'current': True})
    todo = [h for h in daily_habits if h.name not in [d.name for d in completed]]
    todo_by_category = sort_habits_by_category(todo)

    return render_template(
        'habits/index.html',
        completed=completed_by_category,
        todo=todo_by_category,
        long_date=pendulum.now(TZ).strftime(DATE_FORMAT),
    )


@blueprint.route('/completed/', methods=['GET', 'POST'])
def completed():
    """Completed habits."""
    DEFAULT_DATE_FILTER = 'this_week'
    edt = EasyDateTime()
    selected_filter = request.form.get('filter', '') if request.method == 'POST' else DEFAULT_DATE_FILTER
    start_date, end_date = edt.filters.get(selected_filter, (None, None))
    logger.debug(f'date filter: {selected_filter} = {start_date} - {end_date}')

    if start_date is None or end_date is None:
        params = {}
    else:
        params = {'start_date': str(start_date), 'end_date': str(end_date)}

    completed_habits = habits_completed_api.get_many(params=params)
    if completed_habits:
        completed_count = len(completed_habits)
        chart_labels, chart_values = create_completed_habit_chart_data(completed_habits)
    else:
        completed_count = f"No completed habits for time period: {' '.join(selected_filter.split('_')).capitalize()}"
        chart_labels, chart_values = None, None

    daily = habits_api.get_many()

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
    current_habits = habits_api.get_many(params={'current': True})
    hibernating_habits = habits_api.get_many(params={'current': False})
    current_categories = habits_categories_api.get_many(params={'current': True})
    hibernating_categories = habits_categories_api.get_many(params={'current': False})
    completed_habits = habits_completed_api.get_many()
    return render_template(
        'habits/manage.html',
        current_habits=current_habits,
        hibernating_habits=hibernating_habits,
        current_categories=current_categories,
        hibernating_categories=hibernating_categories,
        completed_habits=completed_habits,
    )


@blueprint.route('/crud/', methods=['POST'])
def crud():
    data: dict[str, Any] = request.form.to_dict()
    action = data.pop('action')
    logger.debug(f'{request.referrer=} {action=}')
    logger.debug(f'{data=}')

    match action:
        case 'add_habit':
            habits_api.post(json=data)
            return redirect(request.referrer or url_for('habits.manage'))

        case 'complete_habit':
            data.update({'complete_date': str(pendulum.now(TZ))})
            habits_completed_api.post(json=data)
            return redirect(request.referrer or url_for('habits.manage'))

        case 'hibernate_habit':
            habits_api.patch([data.get('id')], json={'is_current': False})
            return redirect(request.referrer or url_for('habits.manage'))

        case 'revive_habit':
            habits_api.patch([data.get('id')], json={'is_current': True})
            return redirect(request.referrer or url_for('habits.manage'))

        case 'delete_habit':
            habits_api.delete([data.get('id')])
            return redirect(request.referrer or url_for('habits.manage'))

        case 'delete_completed_habit':
            habits_completed_api.delete([data.get('id')])
            return redirect(request.referrer or url_for('habits.manage'))

        case 'add_category':
            habits_categories_api.post(json=data)
            return redirect(request.referrer or url_for('habits.manage'))

        case 'hibernate_category':
            habits_categories_api.patch([data.get('id')], json={'is_current': False})
            return redirect(request.referrer or url_for('habits.manage'))

        case 'revive_category':
            habits_categories_api.patch([data.get('id')], json={'is_current': True})
            return redirect(request.referrer or url_for('habits.manage'))

        case 'delete_category':
            habits_categories_api.delete([data.get('id')])
            return redirect(request.referrer or url_for('habits.manage'))

    return Response(f'Method/Action {action} not accepted', status=status.HTTP_405_METHOD_NOT_ALLOWED)
