from flask import url_for
from markdown import markdown
import os


def md_to_html(md_file):
    with open(f'euphoria/tracks/static/markdown/{md_file}', 'r') as f:
        marks = f.read()
    html = markdown(marks, extensions=['admonition'])
    return html


def get_form_habits(form_dict):
    return {k: v for k, v in form_dict.items() if k not in ('_id', 'date', 'datepicked')}


def _get_habit_categories(habits):
    return list(set(v.get('category') for v in habits.values()))


def _arrange_by_category(habits, category):
    return {k: habits.get(k) for k in habits if habits.get(k).get('category') == category}


def _create_category_dict(habits, categories):
    return {cat: _arrange_by_category(habits, cat) for cat in categories}


def _sort_category_dict(d):
    return {k: d.get(k) for k in sorted(d, key=lambda k: len(d[k]), reverse=True)}


def create_sorted_habit_category_dict(habits):
    categories = _get_habit_categories(habits)
    cat_dict = _create_category_dict(habits, categories)
    return _sort_category_dict(cat_dict)
