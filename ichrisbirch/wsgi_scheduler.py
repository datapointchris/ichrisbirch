import signal
import sys

from ichrisbirch.config import get_settings
from ichrisbirch.scheduler.main import create_scheduler


def exit_on_sigterm(signum, frame):
    sys.exit(0)


# As PID 1 in a container the process ignores SIGTERM unless it installs a handler,
# so `docker stop` would wait out its timeout and kill the scheduler mid-job.
signal.signal(signal.SIGTERM, exit_on_sigterm)
scheduler = create_scheduler(settings=get_settings())
