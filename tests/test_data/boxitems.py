from ichrisbirch.models.boxitem import BoxItem

BASE_DATA: list[BoxItem] = [
    BoxItem(
        box_id=1,
        name='Box 1 - Item 1 of 2 find me',
        essential=True,
        warm=True,
        liquid=True,
    ),
    BoxItem(
        box_id=1,
        name='Box 1 - Item 2 of 2',
        essential=False,
        warm=False,
        liquid=False,
    ),
    BoxItem(
        box_id=2,
        name='Box 2 - Item 1 of 1',
        essential=True,
        warm=True,
        liquid=True,
    ),
]
