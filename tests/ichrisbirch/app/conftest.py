# All Flask pages migrated to Vue — skip entire directory.
# Files preserved for reference during eventual Flask removal.
# API tests that were misplaced here already exist in tests/ichrisbirch/api/endpoints/.
collect_ignore = [
    'test_app_error_handling.py',
    'test_csrf.py',
    'test_login.py',
    'test_utils.py',
    'routes',
]
