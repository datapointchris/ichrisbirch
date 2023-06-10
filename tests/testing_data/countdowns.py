from datetime import date

COUNTDOWN_TEST_DATA = [
    {
        'name': 'Task 1 Chore with notes priority 5 not completed',
        'notes': 'Notes for task 1',
        'due_date': date(2020, 4, 24).isoformat(),
    },
    {
        'name': 'Task 2 Home without notes priority 10 not completed',
        'notes': None,
        'due_date': date(2050, 3, 20).isoformat(),
    },
    {
        'name': 'Task 3 Home with notes priority 15 completed',
        'notes': 'Notes for task 3',
        'due_date': date(2050, 1, 20).isoformat(),
    },
]

COUNTDOWN_TEST_CREATE_DATA = {
    'name': 'Task 4 Computer with notes priority 3',
    'notes': 'Notes task 4',
    'due_date': date(2040, 1, 20).isoformat(),
}
