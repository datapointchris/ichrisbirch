# Test the updated server configs
import argparse
import itertools

import requests
from colorama import Fore

ENVIRONMENTS = {
    'dev': {
        'protocols': ['http://'],
        'host_names': [
            '127.0.0.1',
            # '0.0.0.0',
            'localhost',
            'macmini.local',
            'api.macmini.local',
            # 'random.address',
        ],
        'ports': [80, 4000, 4200, 6000, 6200],
    },
    'test': {
        'protocols': ['http://'],
        'host_names': [
            '127.0.0.1',
            '0.0.0.0',
            'localhost',
            'macmini.local',
            'api.macmini.local',
            'random.address',
        ],
        'ports': [80, 4000, 4200, 6000, 6200, 8000, 8200],
    },
    'prod': {
        'protocols': ['http://'],
        'host_names': [
            'ichrisbirch.com',
            'www.ichrisbirch.com',
            # 'www.ichrisbirch.com/tasks',
            'api.ichrisbirch.com',
            # 'api.ichrisbirch.com/health',
            # 'api.ichrisbirch.com/tasks',
        ],
        'ports': [80],
    },
}

STATUS_CODE_COLORS = {
    '200': Fore.GREEN,
    '502': Fore.RED,
    'EXCEPTION': Fore.YELLOW,
    'default': Fore.RED,
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('environment')
    args = parser.parse_args()

    if not (env := ENVIRONMENTS.get(args.environment)):
        print('ENVIRONMENT WRONG: ', env)
    else:
        pings = []
        for proto, host, port in itertools.product(
            env.get('protocols'), env.get('host_names'), env.get('ports')
        ):
            address = f'{proto}{host}:{port}'
            try:
                res = requests.get(address)
                pings.append((address, str(res.status_code)))
            except Exception:
                pings.append((address, 'EXCEPTION'))

        for (address, status) in sorted(pings):
            color = STATUS_CODE_COLORS.get(status, 'default')
            print(f'{color}{address:<40}{status}')
