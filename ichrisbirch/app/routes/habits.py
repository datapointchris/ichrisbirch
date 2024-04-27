import logging

import httpx
from flask import Blueprint, render_template

from ichrisbirch import schemas
from ichrisbirch.app.easy_dates import EasyDateTime
from ichrisbirch.app.helpers import handle_if_not_response_code, url_builder
from ichrisbirch.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)
blueprint = Blueprint('habits', __name__, template_folder='templates/habits', static_folder='static')


HABITS_API_URL = f'{settings.api_url}/habits/'


@blueprint.route('/', methods=['GET', 'POST'])
def index():

    edt = EasyDateTime()
    start_date, end_date = edt.filters.get('today', (None, None))
    params = {'start_date': str(start_date), 'end_date': str(end_date)}

    completed_response = httpx.get(url_builder(HABITS_API_URL, 'completed'), params=params)
    handle_if_not_response_code(200, completed_response, logger)
    completed = [schemas.Habit(**habit) for habit in completed_response.json()]

    daily_response = httpx.get(HABITS_API_URL)
    handle_if_not_response_code(200, daily_response, logger)
    daily = [schemas.Habit(**habit) for habit in daily_response.json()]

    not_completed = [habit for habit in daily if habit not in completed]

    return render_template('habits/index.html', completed_today=completed, not_completed=not_completed)


# @blueprint.route('/completed/', methods=['GET', 'POST'])
# def completed():
#     """Completed habits"""
#     if request.method == 'POST':
#         selected_habit = request.form.get('habit')
#         date_filter = request.form.get('filter')
#     else:
#         selected_habit = None
#         date_filter = 'this_week'

#     with session:
#         q = session.query(CompletedHabit)
#         q = q.join(Habit, CompletedHabit.habit_id == Habit.id)
#         if selected_habit:
#             q = q.where(Habit.name == selected_habit)
#         first_completed = q.order_by(CompletedHabit.completed_date.asc()).first()
#         last_completed = q.order_by(CompletedHabit.completed_date.desc()).first()

#         habits = session.query(Habit).all()

#     ed = EasyDate()
#     filters = {
#         'today': (ed.today, ed.tomorrow),
#         'yesterday': (ed.yesterday, ed.today),
#         'this_week': (ed.week_start, ed.week_end),
#         'last_7': (ed.previous_7, ed.today),
#         'this_month': (ed.this_month, ed.next_month),
#         'last_30': (ed.previous_30, ed.today),
#         'this_year': (ed.this_year, ed.next_year),
#         'all': (first_completed.complete_date, last_completed.complete_date),
#     }

#     start_date, end_date = filters.get(date_filter)

#     with session:
#         q = session.query(CompletedHabit)
#         q = q.where(
#             CompletedHabit.completed_date >= start_date,
#             CompletedHabit.completed_date < end_date,
#         )
#         completed = q.order_by(CompletedHabit.completed_date.desc()).all()

#     return render_template(
#         'habits/completed.html',
#         habits=habits,
#         completed=completed,
#         filters=filters,
#         date_filter=date_filter,
#         long_date=ed.today.strftime('%A %B %d, %Y'),
#     )


# @blueprint.route('/manage/', methods=['GET', 'POST'])
# def manage():
#     """Manage habits page"""
#     if request.method == 'POST':
#         data = request.form.to_dict()
#         action = data.pop('action')
#         habit = Habit(**data)
#         print(action, habit)

#     return render_template('habits/manage.html')


# # TODO: [2023/02/10] - change form to crud
# @blueprint.route('/form/', methods=['POST'])
# def form():
#     """CRUD operations for habits"""
#     api_url = settings.api_url
#     data = request.form.to_dict()
#     action = data.pop('action')
#     match action:
#         case ['add_habit']:
#             habit = Habit(**data)
#             httpx.post(f'{api_url}/habits', data=habit)
#         case ['delete_habit']:
#             habit = Habit(**data)
#             httpx.delete(f'{api_url}/habits/{habit.id}')
#         case ['complete_habit']:
#             habit = Habit(**data)
#             httpx.post(f'{api_url}/habits/completed', data=habit)
#         case ['add_category']:
#             category = Category(**data)
#             httpx.post(f'{api_url}/habits/categories', data=category)
#         case ['delete_category']:
#             category = Category(**data)
#             httpx.delete(f'{api_url}/habits/categories/{category.id}')

#     return redirect(url_for('habits.index'))
