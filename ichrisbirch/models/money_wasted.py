from datetime import date

from sqlalchemy import Date
from sqlalchemy import Float
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column

from ichrisbirch.database.sqlalchemy.base import Base


class MoneyWasted(Base):
    __tablename__ = 'money_wasted'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    item: Mapped[str] = mapped_column(String(64), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    date_purchased: Mapped[date] = mapped_column(Date, nullable=True)
    date_wasted: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    def __repr__(self):
        return (
            f'MoneyWasted(item={self.item}, amount={self.amount}, date_purchased={self.date_purchased}, '
            f'date_wasted={self.date_wasted}, notes={self.notes}'
        )
