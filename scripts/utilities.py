import logging
import subprocess

logger = logging.getLogger(__name__)


def start_process(process):
    """Starts a process if it is not running"""
    if subprocess.run(['pgrep', '-x', process, '>/dev/null']).returncode == 0:
        print(f'{process} is running')
        logger.info(f'{process} is running')
    else:
        print(f'{process} is not running, starting...')
        logger.info(f'{process} is not running, starting...')
        subprocess.run(['open', '-ga', process])
        subprocess.run(['sleep', '30'])
        print(f'{process} started')
        logger.info(f'{process} started')
