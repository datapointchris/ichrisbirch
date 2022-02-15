from euphoria import event_db as db


class Event(db.Model):
    """Data Model for Events Happening"""

    __tablename__ = 'tracks.events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=False, unique=False, nullable=False)
    date = db.Column(db.DateTime, index=False, unique=False, nullable=False)
    venue = db.Column(db.String(64), index=False, unique=False, nullable=False)
    url = db.Column(db.String(256), index=False, unique=False, nullable=True)
    cost = db.Column(db.Float, index=False, unique=False, nullable=False)
    attending = db.Column(db.Boolean, index=False, unique=False, nullable=False)
    notes = db.Column(db.Text, index=False, unique=False, nullable=True)

    def __repr__(self):
        return f'Event(name={self.name}, date={self.date}, url={self.url}, cost={self.cost}, attending={self.attending}, notes={self.notes}'
