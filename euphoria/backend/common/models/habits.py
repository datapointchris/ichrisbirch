from sqlalchemy import Column, Integer, Boolean, String, Date, ForeignKey
from euphoria.backend.common.db.sqlalchemy.base import Base


class Habit(Base):
    __table_args__ = {'schema': 'habits'}
    __tablename__ = 'habits'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class Category(Base):
    __table_args__ = {'schema': 'habits'}
    __tablename__ = 'categories'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)


class CompletedHabit(Base):
    __table_args__ = {'schema': 'habits'}
    __tablename__ = 'completed'
    id = Column(Integer, primary_key=True)
    completed_date = Column(Date, nullable=False)


# class Habit(Base):
#     __table_args__ = {'schema': 'habits'}
#     __tablename__ = 'habits'
#     id = Column(Integer, primary_key=True)
#     name = Column(String, nullable=False)
#     # TODO: This is broken
#     category_id = Column(String, ForeignKey('habits.categories.id'), nullable=False)
#     current = Column(Boolean)

#     def __repr__(self):
#         return (
#             f'Habit(name={self.name!r}, category_id={self.category_id!r}, current={self.current!r})'
#         )


# class Category(Base):
#     __table_args__ = {'schema': 'habits'}
#     __tablename__ = 'categories'
#     id = Column(Integer, primary_key=True)
#     name = Column(String, nullable=False)

#     def __repr__(self):
#         return f'Category(name={self.name!r})'


# class CompletedHabit(Base):
#     __table_args__ = {'schema': 'habits'}
#     __tablename__ = 'completed'
#     id = Column(Integer, primary_key=True)
#     habit_id = Column(Integer, ForeignKey('habits.habits.id'), nullable=False)
#     completed_date = Column(Date, nullable=False)

#     def __repr__(self):
#         return f'CompletedHabit(habit_id={self.habit_id!r}, completed_date={self.completed_date!r})'
