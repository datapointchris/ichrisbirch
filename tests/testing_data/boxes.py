from ichrisbirch.models.box import Box, BoxSize

BASE_DATA: list[Box] = [
    Box(
        name='Box 1 lots of goodies',
        size=BoxSize.SMALL,
        essential=True,
        warm=False,
        liquid=False,
    ),
    Box(
        name='Box 2 full of junk',
        size=BoxSize.MEDIUM,
        essential=False,
        warm=False,
        liquid=False,
    ),
    Box(
        name='Box 3 minimalist maximalist',
        size=BoxSize.MONITOR,
        essential=True,
        warm=True,
        liquid=True,
    ),
]
