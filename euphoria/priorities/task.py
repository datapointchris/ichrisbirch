from flask_sqlalchemy import SQLAlchemy
from flask import Flask
from datetime import datetime
import random

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Task(db.Model):
    """Data Model for Events Happening"""

    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=False, unique=False, nullable=False)
    category = db.Column(db.String(64), index=False, unique=False, nullable=True)
    subcategory1 = db.Column(db.String(64), index=False, unique=False, nullable=True)
    subcategory2 = db.Column(db.String(64), index=False, unique=False, nullable=True)
    priority = db.Column(db.Integer, index=False, unique=False, nullable=False)
    add_date = db.Column(db.DateTime, index=False, unique=False, nullable=False)
    complete_date = db.Column(db.DateTime, index=False, unique=False, nullable=True)

    def __repr__(self):
        return f'''
            Task(name = {self.name}, category = {self.category},
            subcategory1 = {self.subcategory1}, subcategory2 = {self.subcategory2},
            priority = {self.priority}, 
            add_date = {self.add_date}, complete_date = {self.complete_date}
            '''


db.init_app(app)
db.create_all()

top_5_tasks = Task.query.order_by(Task.priority.asc(), Task.add_date.asc()).limit(5).all()
print(top_5_tasks)


completed = (datetime.utcnow(), None, None, None)
for i in range(30):
    t = {
        'name': f'task {i}',
        'category': 'financial',
        'subcategory1': None,
        'subcategory2': None,
        'priority': random.randint(0, 100),
        'add_date': datetime.utcnow(),
        'complete_date': random.choice(completed),
    }
    db.session.add(Task(**t))

db.session.commit()
