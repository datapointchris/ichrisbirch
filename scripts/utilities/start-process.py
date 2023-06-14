import subprocess

import click


@click.command()
@click.option('--process', help='Process to check')
def start_process(process):
    if subprocess.run(['pgrep', '-x', process, '>/dev/null']).returncode == 0:
        print(f'{process} is running')
    else:
        print(f'{process} is not running, starting...')
        subprocess.run(['open', '-ga', process])
        subprocess.run(['sleep', '30'])
        print(f'{process} started')


if __name__ == '__main__':
    start_process()
