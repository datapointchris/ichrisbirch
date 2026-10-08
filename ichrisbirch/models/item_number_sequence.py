from sqlalchemy import Sequence

from ichrisbirch.database.base import Base

# One sequence numbers both project items and issues, so a bare number names
# exactly one row whichever of the two tables holds it.
ITEM_NUMBER_SEQUENCE = Sequence('item_numbers', metadata=Base.metadata)
