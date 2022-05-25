from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for
from sqlalchemy import select, update, delete
from euphoria import mongodb, db
from euphoria.tracks.helpers import (
    md_to_html,
    get_form_habits,
    create_sorted_habit_category_dict,
)
from euphoria.tracks.models import Event, Deadline
from euphoria.tracks.mongo import (
    HabitsMongoManager,
    JournalMongoManager,
)

habits_db = HabitsMongoManager(mongodb)
journal_db = JournalMongoManager(mongodb)

tracks_bp = Blueprint(
    'tracks_bp', __name__, template_folder='templates/tracks', static_folder='static'
)


@tracks_bp.route('/')
def todo():
    todo = md_to_html('todo.md')
    big_todo = md_to_html('big_todo_list.md')
    goals = md_to_html('goals.md')
    new_apt_checklist = md_to_html('new_apt_checklist.md')
    events = db.session.execute(select(Event).order_by(Event.date)).scalars().all()
    deadlines = (
        db.session.execute(select(Deadline).order_by(Deadline.date)).scalars().all()
    )
    return render_template(
        'todo.html',
        todo=todo,
        big_todo=big_todo,
        goals=goals,
        new_apt_checklist=new_apt_checklist,
        events=events,
        deadlines=deadlines,
    )


# ==================== Habits ==================== #


@tracks_bp.route('/habits/', methods=['GET', 'POST'])
def habits():
    if request.method == 'POST':
        date = request.form.get('date')
        datepicked = request.form.get('datepicked')
        if datepicked:
            habits = habits_db.get_habits_for_date(date)
            if not habits:
                habits = habits_db.get_current_habits()
        else:
            form_habits = get_form_habits(request.values)
            habits = habits_db.append_habit_categories(form_habits)
            print(habits)
            habits_db.record_daily_habits(date, habits)
    else:
        date = datetime.today().strftime("%Y-%m-%d")
        habits = habits_db.get_habits_for_date(date)
        if not habits:
            habits = habits_db.get_current_habits()

    long_date = datetime.strptime(date, "%Y-%m-%d").strftime('%A %B %d, %Y')
    habit_tasks = md_to_html('current_habits.md')
    categories = create_sorted_habit_category_dict(habits)
    current_habits = habits_db.get_current_habits()
    current_categories = create_sorted_habit_category_dict(current_habits)
    return render_template(
        'habits.html',
        date=date,
        long_date=long_date,
        categories=categories,
        current_categories=current_categories,
        habit_tasks=habit_tasks,
    )


@tracks_bp.route('/add_habit/', methods=['POST'])
def add_habit():
    habit = request.form.get('habit_name')
    category = request.form.get('habit_category')
    new_habit = {habit: {'checked': 0, 'category': category}}
    habits_db.add_habit(new_habit)
    habits_db.add_to_master_habit_list(new_habit)
    return redirect(url_for('tracks_bp.habits'))


@tracks_bp.route('/delete_habit/', methods=['POST'])
def delete_habit():
    habit = request.form.get('habit_name')
    category = request.form.get('habit_category')
    new_habit = {habit: {'checked': 0, 'category': category}}
    habits_db.delete_habit(new_habit)
    return redirect(url_for('tracks_bp.habits'))


# ==================== Journal ==================== #


@tracks_bp.route('/add_journal_entry/', methods=['POST'])
def journal_entry():
    # TODO: Journal Entry class
    date = request.form.get('journalDate')
    entry = request.form.get('entry')
    feeling = request.form.get('feeling')
    new_entry = {'date': date, 'entry': entry, 'feeling': feeling}
    print('Entry:', new_entry)
    journal_db.add_journal_entry(new_entry)
    return redirect(url_for('tracks_bp.habits'))


@tracks_bp.route('/reference/')
def reference():
    stretching = md_to_html('stretching.md')
    yoga_stretching = md_to_html('yoga_stretching.md')
    yoga_workout = md_to_html('yoga_workout.md')
    return render_template(
        'reference.html',
        stretching=stretching,
        yoga_stretching=yoga_stretching,
        yoga_workout=yoga_workout,
    )


# ==================== Countdowns ==================== #


@tracks_bp.route('/countdowns/', methods=['GET', 'POST'])
def countdowns():
    deadlines = (
        db.session.execute(select(Deadline).order_by(Deadline.date)).scalars().all()
    )
    return render_template('countdowns.html', deadlines=deadlines)


@tracks_bp.route('/deadlines/', methods=['POST'])
def deadlines():
    deadline = {**request.form}
    if deadline.get('add'):
        deadline.pop('add')
        db.session.add(Deadline(**deadline))
    if deadline.get('delete'):
        deadline.pop('delete')
        db.session.execute(delete(Deadline).where(Deadline.name == deadline.get('name')))
    db.session.commit()
    return redirect(url_for('tracks_bp.countdowns'))


# ==================== Events ==================== #


@tracks_bp.route('/manage_events/', methods=['GET', 'POST'])
def manage_events():
    if request.method == 'POST':
        # TODO: Use the Event class, fix date somewhere else
        event = dict(
            name=request.form.get('name'),
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d'),
            venue=request.form.get('venue'),
            url=request.form.get('url'),
            cost=request.form.get('cost'),
            attending=True if request.form.get('attending') == '1' else False,
            notes=request.form.get('notes'),
        )
        if request.form.get('add'):
            db.session.add(Event(**event))
        elif request.form.get('update'):
            db.session.execute(
                update(Event).where(Event.name == event.get('name')).values(**event)
            )
        elif request.form.get('delete'):
            db.session.execute(delete(Event).where(Event.name == event.get('name')))
        db.session.commit()
    events = db.session.execute(select(Event).order_by(Event.date)).scalars().all()
    return render_template('manage_events.html', events=events)


# This is for testing position of buttons and home nav
@tracks_bp.route('/position/')
def position():
    return render_template('position.html')
