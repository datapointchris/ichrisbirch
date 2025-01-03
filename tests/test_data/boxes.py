from ichrisbirch.models.box import Box
from ichrisbirch.models.box import BoxSize

BASE_DATA: list[Box] = [
    Box(
        name='Box 1 lots of goodies',
        number=1,
        size=BoxSize.Small,
        essential=True,
        warm=False,
        liquid=True,
    ),
    Box(
        name='Box 2 full of junk',
        number=2,
        size=BoxSize.Medium,
        essential=True,
        warm=True,
        liquid=True,
    ),
    Box(
        name='Box 3 minimalist maximalist',
        number=3,
        size=BoxSize.Monitor,
        essential=False,
        warm=False,
        liquid=False,
    ),
]
