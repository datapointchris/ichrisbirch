from sqlalchemy import Column, Float, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import relationship
from ichrisbirch.db.sqlalchemy.base import Base


class Apartment(Base):
    __table_args__ = {'schema': 'apartments'}
    __tablename__ = 'apartments'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    address = Column(String)
    url = Column(String)
    notes = Column(String)
    features = relationship('Feature', back_populates='apartment', cascade='all, delete')

    def __repr__(self):
        return f'''Apartment(name={self.name!r}, address={self.address!r},
            url={self.url!r}, notes={self.notes!r}'''


class Feature(Base):
    __table_args__ = {'schema': 'apartments'}
    __tablename__ = 'features'
    id = Column(Integer, primary_key=True, index=True)
    apt_id = Column(Integer, ForeignKey('apartments.apartments.id'), nullable=False)
    name = Column(String)
    value_bool = Column(Boolean, nullable=True)
    value_str = Column(String, nullable=True)
    value_int = Column(Integer, nullable=True)
    value_float = Column(Float, nullable=True)
    apartment = relationship('Apartment', back_populates='features')

    def __repr__(self):
        return f'''Feature(name={self.name!r}, apt_id={self.apt_id!r},
            value_bool={self.value_bool!r}, value_str={self.value_str!r},
            value_int={self.value_int!r}, value_float={self.value_float!r}, notes={self.notes!r}'''
