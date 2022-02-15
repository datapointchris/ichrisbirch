import datetime

from flask import Blueprint, render_template, request, redirect, url_for
import sqlalchemy
from euphoria import habit_db, journal_db, countdown_db, event_db
from euphoria.tracks.helpers import (
    md_to_html,
    get_form_habits,
    create_sorted_habit_category_dict,
)
from euphoria.tracks.models import Event

tracks_bp = Blueprint(
    'tracks_bp', __name__, template_folder='templates/tracks', static_folder='static'
)


@tracks_bp.route('/')
def todo():
    todo = md_to_html('todo.md')
    big_todo = md_to_html('big_todo_list.md')
    goals = md_to_html('goals.md')
    new_apt_checklist = md_to_html('new_apt_checklist.md')
    events = (
        event_db.session.execute(sqlalchemy.select(Event).order_by(Event.date))
        .scalars()
        .all()
    )
    deadlines = countdown_db.get_countdowns()
    return render_template(
        'todo.html',
        todo=todo,
        big_todo=big_todo,
        goals=goals,
        new_apt_checklist=new_apt_checklist,
        events=events,
        deadlines=deadlines,
    )


@tracks_bp.route('/habits/', methods=['GET', 'POST'])
def habits():
    if request.method == 'POST':
        date = request.form.get('date')
        datepicked = request.form.get('datepicked')
        if datepicked:
            print('POST')
            print(f'{date=}')
            print('datepicked SET')
            habits = habit_db.get_habits_for_date(date)
            if not habits:
                habits = habit_db.get_current_habits()
        else:
            print('POST')
            print(f'{date=}')
            print('datepicked Empty')
            form_habits = get_form_habits(request.values)
            habits = habit_db.append_habit_categories(form_habits)
            print(habits)
            habit_db.record_daily_habits(date, habits)
    else:
        date = datetime.datetime.today().strftime("%Y-%m-%d")
        habits = habit_db.get_habits_for_date(date)
        if not habits:
            habits = habit_db.get_current_habits()
        print('GET')
        print(f'{date=}')
        print(habits)
    long_date = datetime.datetime.strptime(date, "%Y-%m-%d").strftime('%A %B %d, %Y')
    habit_tasks = md_to_html('current_habits.md')
    categories = create_sorted_habit_category_dict(habits)
    current_habits = habit_db.get_current_habits()
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
    habit_db.add_habit(new_habit)
    habit_db.add_to_master_habit_list(new_habit)
    return redirect(url_for('tracks_bp.habits'))


@tracks_bp.route('/delete_habit/', methods=['POST'])
def delete_habit():
    habit = request.form.get('habit_name')
    category = request.form.get('habit_category')
    new_habit = {habit: {'checked': 0, 'category': category}}
    habit_db.delete_habit(new_habit)
    return redirect(url_for('tracks_bp.habits'))


@tracks_bp.route('/add_journal_entry/', methods=['POST'])
def journal_entry():
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


@tracks_bp.route('/countdowns/', methods=['GET', 'POST'])
def countdowns():
    countdowns = countdown_db.get_countdowns()
    countdowns = countdown_db.remove_time_from_dates(countdowns)
    return render_template('countdowns.html', countdowns=countdowns)


@tracks_bp.route('/add_countdown/', methods=['POST'])
def add_countdown():
    name = request.form.get('name')
    date = request.form.get('date')
    date = datetime.datetime.strptime(date, '%Y-%m-%d')
    name_id = countdown_db.make_countdown_id_from_name(name)
    countdown = {'name': name, 'date': date, 'name_id': name_id}
    countdown_db.add_countdown(countdown)
    return redirect(url_for('tracks_bp.countdowns'))


@tracks_bp.route('/delete_countdown/', methods=['POST'])
def delete_countdown():
    name = request.form.get('name')
    date = request.form.get('date')
    date = datetime.datetime.strptime(date, '%B %d %Y')
    name_id = request.form.get('name_id')
    countdown = {'name': name, 'date': date, 'name_id': name_id}
    print(countdown)
    countdown_db.delete_countdown(countdown)
    return redirect(url_for('tracks_bp.countdowns'))


@tracks_bp.route('/manage_events/', methods=['GET', 'POST'])
def manage_events():
    if request.method == 'POST':
        add = request.form.get('add')
        update = request.form.get('update')
        delete = request.form.get('delete')
        event = dict(
            name=request.form.get('name'),
            date=datetime.datetime.strptime(request.form.get('date'), '%Y-%m-%d'),
            url=request.form.get('url'),
            cost=request.form.get('cost'),
            attending=True if request.form.get('attending') == '1' else False,
            notes=request.form.get('notes'),
        )
        if add:
            event_db.session.add(Event(**event))
        elif update:
            event_db.session.execute(
                sqlalchemy.update(Event)
                .where(Event.name == event.get('name'))
                .values(**event)
            )
        elif delete:
            event_db.session.execute(
                sqlalchemy.delete(Event).where(Event.name == event.get('name'))
            )
        event_db.session.commit()
    events = (
        event_db.session.execute(sqlalchemy.select(Event).order_by(Event.date))
        .scalars()
        .all()
    )
    return render_template('manage_events.html', events=events)


# This is for testing position of buttons and home nav
@tracks_bp.route('/position/')
def position():
    return render_template('position.html')
