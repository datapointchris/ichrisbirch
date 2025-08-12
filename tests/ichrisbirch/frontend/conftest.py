import pytest


def pytest_runtest_makereport(item, call):
    # Hook for each test phase (setup, call, teardown)
    # Mark the directory for skipping if there's a failure in a frontend test
    if all(
        [
            call.when == 'call',  # happens during the test execution phase
            call.excinfo is not None,  # there was an exception
            'frontend' in item.fspath.dirname,  # we are in the frontend test directory
        ]
    ):
        item.session.frontend_should_skip = True


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    # Skip tests in the frontend if a previous test failed
    if 'frontend' in item.fspath.dirname and getattr(item.session, 'frontend_should_skip', False):
        pytest.skip('Skipping due to a previous test failure in the frontend directory.')
