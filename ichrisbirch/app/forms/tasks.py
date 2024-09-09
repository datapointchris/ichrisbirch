from flask_wtf import FlaskForm
from wtforms import DateTimeField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import NumberRange
from wtforms.validators import Optional

from ichrisbirch.app.routes.tasks import TASK_CATEGORIES

category_choices = [(c, c) for c in TASK_CATEGORIES]


class TaskCreateForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Optional()], render_kw={'rows': 1})
    category = SelectField('Category', choices=category_choices, validators=[DataRequired()])
    priority = IntegerField('Priority', validators=[DataRequired(), NumberRange(min=1)])


class TaskUpdateForm(FlaskForm):
    name = StringField('Name', validators=[Optional()])
    notes = TextAreaField('Notes', validators=[Optional()], render_kw={'rows': 3})
    category = SelectField('Category', choices=category_choices, validators=[Optional()])
    priority = IntegerField('Priority', validators=[Optional()])
    add_date = DateTimeField('Add Date', validators=[Optional()])
    complete_date = DateTimeField('Complete Date', validators=[Optional()])
