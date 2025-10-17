from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms import DateField
from wtforms import FloatField
from wtforms import IntegerField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms.validators import URL
from wtforms.validators import DataRequired
from wtforms.validators import Optional


class BookCreateForm(FlaskForm):
    isbn = StringField('ISBN', validators=[DataRequired()])
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
    abandoned = BooleanField('Abandoned', validators=[Optional()])
    location = StringField('Location', validators=[Optional()])
    notes = TextAreaField('Notes', render_kw={'rows': 3}, validators=[Optional()])


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
    abandoned = BooleanField('Abandoned', validators=[Optional()])
    location = StringField('Location', validators=[Optional()])
    notes = TextAreaField('Notes', render_kw={'rows': 3}, validators=[Optional()])
