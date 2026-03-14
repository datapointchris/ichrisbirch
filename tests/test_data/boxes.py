from ichrisbirch.models.box import Box
from ichrisbirch.models.boxitem import BoxItem

BASE_DATA: list[Box] = [
    Box(
        name='Box 1 lots of goodies',
        number=1,
        size='Small',
        essential=True,
        warm=False,
        liquid=True,
        items=[
            BoxItem(name='Box 1 - Item 1 of 2 find me', essential=True, warm=True, liquid=True),
            BoxItem(name='Box 1 - Item 2 of 2', essential=False, warm=False, liquid=False),
        ],
    ),
    Box(
        name='Box 2 full of junk',
        number=2,
        size='Medium',
        essential=True,
        warm=True,
        liquid=True,
        items=[
            BoxItem(name='Box 2 - Item 1 of 1', essential=True, warm=True, liquid=True),
        ],
    ),
    Box(
        name='Box 3 minimalist maximalist',
        number=3,
        size='Monitor',
        essential=False,
        warm=False,
        liquid=False,
    ),
]
