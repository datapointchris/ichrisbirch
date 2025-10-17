#!/usr/bin/env python

# Test the updated server configs
import argparse
import itertools

import httpx
from colorama import Fore

ENVIRONMENTS = {
    'dev': {
        'protocols': ['http://'],
        'host_names': [
            '127.0.0.1',
            '0.0.0.0',
            'localhost',
            # 'macmini.local',
            # 'api.macmini.local',
            # 'random.address',
        ],
        'endpoints': [
            '',
            # '/tasks',
            # '/server',
        ],
        'ports': ['', ':80', ':4000', ':4200', ':6000', ':6200', ':5434', ':5555'],
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
        'endpoints': ['', '/tasks', '/server'],
        'ports': ['', ':80', ':4000', ':4200', ':6000', ':6200', ':8000', ':8200'],
    },
    'prod': {
        'protocols': ['', 'http://'],
        'host_names': [
            'ichrisbirch.com',
            'www.ichrisbirch.com',
            'api.ichrisbirch.com',
        ],
        'endpoints': ['', '/tasks', '/server'],
        'ports': ['', ':80'],
    },
}

STATUS_CODE_COLORS = {
    '200': Fore.GREEN,
    '404': Fore.RED,
    '502': Fore.RED,
    'EXCEPTION': Fore.YELLOW,
    'default': Fore.RED,
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('environment')
    args = parser.parse_args()

    if not (env := ENVIRONMENTS.get(args.environment)):
        print(f'{Fore.RED}Unrecognized ENVIRONMENT: {env}')
    else:
        pings = []
        for protocol, host, endpoint, port in itertools.product(env['protocols'], env['host_names'], env['endpoints'], env['ports']):
            address = f'{protocol}{host}{endpoint}{port}'
            try:
                res = httpx.get(address, allow_redirects=True)
                pings.append((address, str(res.status_code), ''))
            except Exception as e:
                pings.append((address, 'EXCEPTION', str(e)))

        for address, status, message in sorted(pings):
            color = STATUS_CODE_COLORS.get(status, Fore.RED)
            print(f'{color}{address:<40}{status:<11}{message[:50]}')
