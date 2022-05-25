from euphoria import db


class Event(db.Model):
    __table_args__ = {'schema': 'tracks'}
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), index=False, unique=False, nullable=False)
    date = db.Column(db.DateTime, index=False, unique=False, nullable=False)
    venue = db.Column(db.String(256), index=False, unique=False, nullable=False)
    url = db.Column(db.Text, index=False, unique=False, nullable=True)
    cost = db.Column(db.Float, index=False, unique=False, nullable=False)
    attending = db.Column(db.Boolean, index=False, unique=False, nullable=False)
    notes = db.Column(db.Text, index=False, unique=False, nullable=True)

    def __repr__(self):
        return f'Event(name={self.name}, date={self.date}, url={self.url}, venue={self.venue}, cost={self.cost}, attending={self.attending}, notes={self.notes}'


class Deadline(db.Model):
    __table_args__ = {'schema': 'tracks'}
    __tablename__ = 'deadlines'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), index=False, unique=False, nullable=False)
    date = db.Column(db.DateTime, index=False, unique=False, nullable=False)

    def __repr__(self):
        return f'Deadline(name={self.name}, date={self.date}'
