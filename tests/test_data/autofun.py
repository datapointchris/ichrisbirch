from ichrisbirch.models.autofun import AutoFun

BASE_DATA: list[AutoFun] = [
    AutoFun(
        name='Go to the Japanese Tea Garden',
        notes='Free on weekday mornings',
        is_completed=False,
    ),
    AutoFun(
        name='Hike the Dipsea Trail',
        notes=None,
        is_completed=False,
    ),
    AutoFun(
        name='Watch a film at the Castro Theatre',
        notes='Check schedule for special screenings',
        is_completed=False,
    ),
]
