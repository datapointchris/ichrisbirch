# Test the updated server configs
import argparse
import itertools
from dataclasses import dataclass

import requests
from colorama import Fore


@dataclass
class Environment:
    protocols: list[str]
    host_names: list[str]
    ports: list[str]


ENVIRONMENTS = {
    'dev': Environment(
        **{
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
        }
    ),
    'test': Environment(
        **{
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
        }
    ),
    'prod': Environment(
        **{
            'protocols': ['http://'],
            'host_names': [
                'ichrisbirch.com',
                'www.ichrisbirch.com',
                'api.ichrisbirch.com',
            ],
            'ports': [80],
        }
    ),
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('environment')
    args = parser.parse_args()

    if not (env := ENVIRONMENTS.get(args.environment)):
        print('ENVIRONMENT WRONG: ', env)
    else:
        pings = []
        for proto, host, port in itertools.product(env.protocols, env.host_names, env.ports):
            address = f'{proto}{host}:{port}'
            try:
                res = requests.get(address)
                pings.append((address, str(res.status_code)))
            except Exception:
                pings.append((address, 'EXCEPTION'))

        for test in sorted(pings):
            if test[1] == '200':
                print(f'{Fore.GREEN}{test[0]:<40}{test[1]}')
            elif test[1] == '502':
                print(f'{Fore.RED}{test[0]:<40}{test[1]}')
            elif test[1] == 'EXCEPTION':
                print(f'{Fore.YELLOW}{test[0]:<40}{test[1]}')
                continue
            else:
                print(Fore.RED + 'Unknown Error')
