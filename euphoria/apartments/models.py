from euphoria import db


class Apartment(db.Model):
    __table_args__ = {'schema': 'apartments'}
    __tablename__ = 'apartments'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=False, nullable=False)
    address = db.Column(db.String(256), unique=False, nullable=False)
    url = db.Column(db.String(256), unique=False, nullable=False)
    features = db.relationship('Feature', backref='apartments.apartments')

    def __repr__(self):
        return f'Apartment(name = {self.name}, address = {self.address}, url = {self.url}'


class Feature(db.Model):
    __table_args__ = {'schema': 'apartments'}
    __tablename__ = 'features'
    id = db.Column(db.Integer, primary_key=True)
    apartment_id = db.Column(
        db.Integer, db.ForeignKey('apartments.apartments.id'), nullable=False
    )
    name = db.Column(db.String(64), unique=False, nullable=False)
    type = db.Column(db.String(32), unique=False, nullable=False)
    value = db.Column(db.String)

    def __repr__(self):
        return f'Feature(apartment_id = {self.apartment_id}, name = {self.name}, type = {self.type}, value = {self.value}'
