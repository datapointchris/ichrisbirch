from euphoria import db


class Box(db.Model):
    """Data Model for Box"""

    __table_args__ = {'schema': 'moving'}
    __tablename__ = 'boxes'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=False, nullable=False)
    essential = db.Column(db.Boolean, unique=False, nullable=False)
    warm = db.Column(db.Boolean, unique=False, nullable=False)
    liquid = db.Column(db.Boolean, unique=False, nullable=False)
    items = db.relationship('Item', backref='moving.boxes')

    def __repr__(self):
        return f'Box(name = {self.name}, essential = {self.essential}, warm = {self.warm}, liquid = {self.liquid}'


class Item(db.Model):
    """Data Model for Item"""

    __table_args__ = {'schema': 'moving'}
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    box_id = db.Column(db.Integer, db.ForeignKey('moving.boxes.id'), nullable=False)
    name = db.Column(db.String(64), unique=False, nullable=False)
    essential = db.Column(db.Boolean, unique=False, nullable=False)
    warm = db.Column(db.Boolean, unique=False, nullable=False)
    liquid = db.Column(db.Boolean, unique=False, nullable=False)

    def __repr__(self):
        return f'Item(box_id = {self.box_id}, name = {self.name}, essential = {self.essential}, warm = {self.warm}, liquid = {self.liquid}'
