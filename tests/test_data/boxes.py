from ichrisbirch.models.box import Box
from ichrisbirch.models.box import BoxSize

BASE_DATA: list[Box] = [
    Box(
        name='Box 1 lots of goodies',
        size=BoxSize.Small,
        essential=True,
        warm=False,
        liquid=True,
    ),
    Box(
        name='Box 2 full of junk',
        size=BoxSize.Medium,
        essential=True,
        warm=True,
        liquid=True,
    ),
    Box(
        name='Box 3 minimalist maximalist',
        size=BoxSize.Monitor,
        essential=False,
        warm=False,
        liquid=False,
    ),
]
