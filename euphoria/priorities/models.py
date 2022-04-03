from euphoria import priorities_db as db


class Task(db.Model):
    """Data Model for Events Happening"""

    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=False, unique=False, nullable=False)
    category = db.Column(db.String(64), index=False, unique=False, nullable=True)
    subcategory1 = db.Column(db.String(64), index=False, unique=False, nullable=True)
    subcategory2 = db.Column(db.String(64), index=False, unique=False, nullable=True)
    add_date = db.Column(db.DateTime, index=False, unique=False, nullable=False)
    complete_date = db.Column(db.DateTime, index=False, unique=False, nullable=True)

    def __repr__(self):
        return f'''
            Task(name={self.name}, category={self.category},
            subcategory1={self.subcategory1}, subcategory2={self.subcategory2},
            add_date={self.add_date}, complete_date={self.complete_date}
            '''
