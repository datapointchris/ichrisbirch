from ichrisbirch.models.shopping import ShoppingItem
from ichrisbirch.models.shopping import ShoppingPurchase
from ichrisbirch.models.shopping import ShoppingSection

# Items arrive through `ShoppingSection.items`. Ranks interleave across sections
# on purpose, because the table holds one rank space.
SECTIONS: list[ShoppingSection] = [
    ShoppingSection(
        name='Costco',
        rank=1.0,
        items=[
            ShoppingItem(name='eggs', note='2 dozen', rank=1.0, is_needed=True),
            ShoppingItem(name='paper towels', rank=3.0, is_needed=True),
            ShoppingItem(name='coffee beans', rank=5.0, is_needed=False),
        ],
    ),
    ShoppingSection(
        name='Grocery',
        rank=2.0,
        items=[
            ShoppingItem(name='bananas', rank=2.0, is_needed=True),
            ShoppingItem(name='milk', rank=4.0, is_needed=False),
        ],
    ),
    ShoppingSection(name='Hardware', rank=3.0),
]

PURCHASES: list[ShoppingPurchase] = [
    ShoppingPurchase(item_name='milk', section_name='Grocery'),
    ShoppingPurchase(item_name='coffee beans', section_name='Costco'),
    ShoppingPurchase(item_name='butter', note='unsalted', section_name='Grocery'),
]
