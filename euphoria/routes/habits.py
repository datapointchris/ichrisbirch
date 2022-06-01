from flask import Blueprint, render_template, request, current_app, url_for, redirect
from ..models.habits import Habit, Category, CompletedHabit
from ..database.sqlalchemy import session
from datetime import date, timedelta
import calendar
import requests

blueprint = Blueprint(
    'habits', __name__, template_folder='templates/habits', static_folder='static'
)


@blueprint.route('/', methods=['GET', 'POST'])
def index():
    with session:
        current_habits = session.query(Habit).where(Habit.current.is_(True))
        completed_today = session.query(CompletedHabit).where(
            CompletedHabit.completed_date == date.today()
        )
        not_completed = session.query(Habit).join()

    return render_template(
        'index.html', completed_today=completed_today, not_completed=not_completed
    )


@blueprint.route('/completed/', methods=['GET', 'POST'])
def completed():
    if request.method == 'POST':
        selected_habit = request.form.get('habit')
        date_filter = request.form.get('filter')
    else:
        selected_habit = None
        date_filter = 'this_week'
    # Easy to use dates for filters
    today = date.today()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)
    previous_7 = today - timedelta(days=7)
    previous_30 = today - timedelta(days=30)
    _month_days = calendar.monthrange(today.year, today.month)[1]
    _week_number = today.isocalendar().week
    week_start = date.fromisocalendar(today.year, _week_number, 1)
    week_end = week_start + timedelta(days=7)
    this_month = date(today.year, today.month, 1)
    next_month = this_month + timedelta(days=_month_days)
    this_year = date(today.year, 1, 1)
    next_year = date(today.year + 1, 1, 1)

    with session:
        q = session.query(CompletedHabit)
        q = q.join(Habit, CompletedHabit.habit_id == Habit.id)
        if selected_habit:
            q = q.where(Habit.name == selected_habit)
        first_completed = q.order_by(CompletedHabit.completed_date.asc()).first()
        last_completed = q.order_by(CompletedHabit.completed_date.desc()).first()

        habits = session.query(Habit).all()

    filters = {
        'today': (today, tomorrow),
        'yesterday': (yesterday, today),
        'this_week': (week_start, week_end),
        'last_7': (previous_7, today),
        'this_month': (this_month, next_month),
        'last_30': (previous_30, today),
        'this_year': (this_year, next_year),
        'all': (first_completed.complete_date, last_completed.complete_date),
    }

    date_filter_start, date_filter_end = filters.get(date_filter)

    with session:
        q = session.query(CompletedHabit)
        q = q.where(
            CompletedHabit.completed_date >= date_filter_start,
            CompletedHabit.completed_date < date_filter_end,
        )
        completed = q.order_by(CompletedHabit.completed_date.desc()).all()

    return render_template(
        'habits/completed.html',
        habits=habits,
        completed=completed,
        filters=filters,
        date_filter=date_filter,
        long_date=today.strftime('%A %B %d, %Y'),
    )


@blueprint.route('/manage/', methods=['GET', 'POST'])
def manage():
    if request.method == 'POST':
        data = request.form.to_dict()
        method = data.pop('method')
        habit = Habit(**data)

    return render_template('habits/manage.html')


@blueprint.route('/form/', methods=['POST'])
def form():
    api_url = current_app.config.get('API_URL')
    data = request.form.to_dict()
    method = data.pop('method')
    match method:
        case ['add_habit']:
            habit = Habit(**data)
            response = requests.post(f'{api_url}/habits', data=habit)
        case ['delete_habit']:
            habit = Habit(**data)
            response = requests.delete(f'{api_url}/habits/{habit.id}')
        case ['complete_habit']:
            habit = Habit(**data)
            response = requests.post(f'{api_url}/habits/completed', data=habit)
        case ['add_category']:
            category = Category(**data)
            response = requests.post(f'{api_url}/habits/categories', data=category)
        case ['delete_category']:
            category = Category(**data)
            response = requests.delete(f'{api_url}/habits/categories/{category.id}')

    return redirect(url_for('habits.index'))
