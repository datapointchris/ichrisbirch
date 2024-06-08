from datetime import datetime

from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DateTimeField
from wtforms import IntegerField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms.validators import URL
from wtforms.validators import DataRequired

from ichrisbirch.app.forms.validators import RequiredIf


class ArticleCreateForm(FlaskForm):
    url = StringField('URL', validators=[DataRequired(), URL()])
    title = StringField('Title', validators=[DataRequired()])
    tags = StringField('Tags', validators=[DataRequired()])
    summary = TextAreaField('Summary', render_kw={'rows': 6})
    notes = TextAreaField('Notes', render_kw={'rows': 3})
    save_date = DateTimeField('Save Date', default=datetime.now())


class ArticleUpdateForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    tags = StringField('Tags')
    summary = TextAreaField('Summary', render_kw={'rows': 6})
    notes = TextAreaField('Notes', render_kw={'rows': 3})
    is_favorite = BooleanField('Favorite')
    is_current = BooleanField('Current')
    is_archived = BooleanField('Archived')
    review_days = IntegerField('Review Days', validators=[RequiredIf('is_favorite')])
