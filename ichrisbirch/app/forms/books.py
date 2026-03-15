from flask_wtf import FlaskForm
from wtforms import DateField
from wtforms import FloatField
from wtforms import IntegerField
from wtforms import SelectField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms.validators import URL
from wtforms.validators import DataRequired
from wtforms.validators import Optional

OWNERSHIP_CHOICES = [(s, s) for s in ('owned', 'to_purchase', 'rejected', 'sold', 'donated')]
PROGRESS_CHOICES = [(s, s) for s in ('unread', 'reading', 'read', 'abandoned')]


class BookCreateForm(FlaskForm):
    isbn = StringField('ISBN', validators=[Optional()])
    title = StringField('Title', validators=[DataRequired()])
    author = StringField('Author', validators=[DataRequired()])
    tags = StringField('Tags', validators=[DataRequired()])
    goodreads_url = StringField('Goodreads URL', validators=[Optional(), URL()])
    priority = IntegerField('Priority', validators=[Optional()])
    purchase_date = DateField('Purchase Date', validators=[Optional()], render_kw={'type': 'date'})
    purchase_price = FloatField('Purchase Price', validators=[Optional()])
    sell_date = DateField('Sell Date', validators=[Optional()], render_kw={'type': 'date'})
    sell_price = FloatField('Sell Price', validators=[Optional()])
    read_start_date = DateField('Read Start Date', validators=[Optional()], render_kw={'type': 'date'})
    read_finish_date = DateField('Read Finish Date', validators=[Optional()], render_kw={'type': 'date'})
    rating = IntegerField('Rating', validators=[Optional()])
    location = StringField('Location', validators=[Optional()])
    notes = TextAreaField('Notes', render_kw={'rows': 3}, validators=[Optional()])
    ownership = SelectField('Ownership', choices=OWNERSHIP_CHOICES, default='owned', validators=[DataRequired()])
    progress = SelectField('Progress', choices=PROGRESS_CHOICES, default='unread', validators=[DataRequired()])
    reject_reason = TextAreaField('Reject Reason', render_kw={'rows': 2}, validators=[Optional()])


class BookUpdateForm(FlaskForm):
    isbn = StringField('ISBN', validators=[Optional()])
    title = StringField('Title', validators=[Optional()])
    author = StringField('Author', validators=[DataRequired()])
    tags = StringField('Tags', validators=[Optional()])
    goodreads_url = StringField('Goodreads URL', validators=[Optional(), URL()])
    priority = IntegerField('Priority', validators=[Optional()])
    purchase_date = DateField('Purchase Date', validators=[Optional()], render_kw={'type': 'date'})
    purchase_price = FloatField('Purchase Price', validators=[Optional()])
    sell_date = DateField('Sell Date', validators=[Optional()], render_kw={'type': 'date'})
    sell_price = FloatField('Sell Price', validators=[Optional()])
    read_start_date = DateField('Read Start Date', validators=[Optional()], render_kw={'type': 'date'})
    read_finish_date = DateField('Read Finish Date', validators=[Optional()], render_kw={'type': 'date'})
    rating = IntegerField('Rating', validators=[Optional()])
    location = StringField('Location', validators=[Optional()])
    notes = TextAreaField('Notes', render_kw={'rows': 3}, validators=[Optional()])
    ownership = SelectField('Ownership', choices=OWNERSHIP_CHOICES, validators=[Optional()])
    progress = SelectField('Progress', choices=PROGRESS_CHOICES, validators=[Optional()])
    reject_reason = TextAreaField('Reject Reason', render_kw={'rows': 2}, validators=[Optional()])
