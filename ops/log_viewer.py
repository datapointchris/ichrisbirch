"""Structured log viewer for ichrisbirch dev/testing/prod docker logs.

Streams `docker compose logs --follow`, parses structlog JSON output, and
renders with filtering and color. Non-JSON lines (postgres, redis, traefik,
uvicorn startup) fall through with service-name colorization.

Usage examples:
    uv run cli/log_viewer.py dev
    uv run cli/log_viewer.py dev api
    uv run cli/log_viewer.py dev --level WARNING
    uv run cli/log_viewer.py dev --request-id a1b2c3d4
    uv run cli/log_viewer.py dev --module TasksStore --event 'task_'
    uv run cli/log_viewer.py dev --json | jq 'select(.level == "error")'
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console
from rich.text import Text

LEVEL_RANK = {'debug': 10, 'info': 20, 'warning': 30, 'error': 40, 'critical': 50}

LEVEL_STYLE = {
    'debug': 'grey50',
    'info': 'cyan',
    'warning': 'yellow',
    'error': 'bold red',
    'critical': 'bold white on red',
}

SERVICE_STYLE = {
    'api': 'bright_green',
    'vue': 'bright_blue',
    'chat': 'orange1',
    'scheduler': 'yellow',
    'traefik': 'cyan',
    'redis': 'red',
    'postgres': 'green',
    'db': 'green',
    'mcp': 'magenta',
}

ANSI_RE = re.compile(r'\x1b\[[0-9;]*[A-Za-z]')
PREFIX_RE = re.compile(r'^([A-Za-z0-9_.-]+)\s*\|\s?(.*)$')
CONTAINER_STRIP_RE = re.compile(r'^icb-(?:dev|test|prod|blue|green|infra)-')

META_KEYS = {'timestamp', 'level', 'event', 'filename', 'func_name', 'lineno'}


@dataclass
class Filters:
    level_rank: int = 0
    module: str | None = None
    request_id: str | None = None
    event: str | None = None
    grep: re.Pattern[str] | None = None
    services: set[str] | None = None


def short_service(container: str) -> str:
    return CONTAINER_STRIP_RE.sub('', container).strip()


def parse_prefix(line: str) -> tuple[str, str]:
    m = PREFIX_RE.match(line)
    if not m:
        return '', line
    return short_service(m.group(1)), m.group(2)


def try_parse_json(content: str) -> dict | None:
    stripped = content.lstrip()
    if not stripped.startswith('{'):
        return None
    try:
        obj = json.loads(stripped)
    except json.JSONDecodeError:
        return None
    return obj if isinstance(obj, dict) and 'event' in obj else None


def passes_filters(entry: dict | None, raw: str, service: str, filters: Filters) -> bool:
    if filters.services and service and service not in filters.services:
        return False

    if entry is None:
        has_structured = filters.level_rank or filters.module or filters.request_id or filters.event
        if has_structured:
            return False
        return not filters.grep or bool(filters.grep.search(raw))

    if filters.level_rank:
        entry_rank = LEVEL_RANK.get(str(entry.get('level', '')).lower(), 0)
        if entry_rank < filters.level_rank:
            return False
    if filters.module and filters.module.lower() not in str(entry.get('module', '')).lower():
        return False
    if filters.request_id and entry.get('request_id') != filters.request_id:
        return False
    if filters.event and filters.event.lower() not in str(entry.get('event', '')).lower():
        return False
    return not filters.grep or bool(filters.grep.search(raw))


def format_val(v: object) -> str:
    if isinstance(v, str):
        return v if ' ' not in v else json.dumps(v)
    return json.dumps(v, default=str)


def render_structured(console: Console, service: str, entry: dict, no_callsite: bool) -> None:
    ts = str(entry.get('timestamp', ''))
    time_str = ts[11:19] if len(ts) >= 19 and ts[10:11] == 'T' else ts[-8:]
    level = str(entry.get('level', '')).lower() or 'info'
    event = str(entry.get('event', ''))

    svc_style = SERVICE_STYLE.get(service, 'white')
    lvl_style = LEVEL_STYLE.get(level, 'white')

    context_items = []
    if entry.get('module'):
        context_items.append(('module', entry['module']))
    for k, v in entry.items():
        if k in META_KEYS or k == 'module':
            continue
        if v is None:
            continue
        context_items.append((k, v))

    ctx = ' '.join(f'{k}={format_val(v)}' for k, v in context_items)

    text = Text()
    text.append(f'{time_str} ', style='grey50')
    text.append(f'{service:<9} ', style=svc_style)
    text.append(f'{level.upper():<7} ', style=lvl_style)
    text.append(f'{event:<32} ', style='bold')
    text.append(ctx)

    if not no_callsite and entry.get('filename'):
        fn = entry['filename']
        lineno = entry.get('lineno', '')
        func = entry.get('func_name', '')
        suffix = f'  ({fn}:{lineno} {func})' if func else f'  ({fn}:{lineno})'
        text.append(suffix, style='grey50')

    console.print(text, soft_wrap=True, highlight=False)

    exc = entry.get('exception')
    if exc:
        console.print(Text(str(exc), style='red'), soft_wrap=True, highlight=False)


def render_passthrough(console: Console, service: str, raw: str) -> None:
    svc_style = SERVICE_STYLE.get(service, 'white')
    text = Text()
    text.append(f'{service:<9} ', style=svc_style)
    text.append(raw)
    console.print(text, soft_wrap=True, highlight=False)


def build_compose_cmd(env: str, tail: int, follow: bool, services: list[str]) -> list[str]:
    project_root = Path(__file__).resolve().parent.parent
    base = ['docker', 'compose']

    if env == 'dev':
        base += ['--project-name', 'icb-dev', '-f', 'docker-compose.yml', '-f', 'docker-compose.dev.yml']
    elif env == 'testing':
        base += ['--project-name', 'icb-test', '-f', 'docker-compose.yml', '-f', 'docker-compose.test.yml']
    elif env == 'prod':
        color = read_bluegreen_color()
        if color:
            base += ['--project-name', f'icb-{color}', '-f', 'docker-compose.app.yml']
            os.environ['DEPLOY_COLOR'] = color
        else:
            base += ['--project-name', 'icb-prod', '-f', 'docker-compose.yml']
    else:
        raise SystemExit(f'Unknown environment: {env!r} (expected dev|testing|prod)')

    base += ['logs', f'--tail={tail}']
    if follow:
        base.append('--follow')
    base += services
    return [str(project_root)] + base  # cwd + command


def read_bluegreen_color() -> str:
    state_file = Path('/var/lib/ichrisbirch/bluegreen-state')
    try:
        return state_file.read_text().strip()
    except (FileNotFoundError, PermissionError):
        return ''


def stream_logs(cmd_with_cwd: list[str]) -> subprocess.Popen:
    cwd, *cmd = cmd_with_cwd
    return subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        bufsize=1,
        text=True,
    )


def process_stream(proc: subprocess.Popen, console: Console, filters: Filters, no_callsite: bool, raw_json: bool) -> None:
    if proc.stdout is None:
        raise RuntimeError('docker compose logs subprocess has no stdout — was it spawned with stdout=subprocess.PIPE?')
    for line in proc.stdout:
        line = line.rstrip('\n')
        if not line:
            continue
        line = ANSI_RE.sub('', line)
        service, rest = parse_prefix(line)
        entry = try_parse_json(rest)

        if not passes_filters(entry, rest, service, filters):
            continue

        if raw_json and entry is not None:
            # Re-emit as a flat JSON line with the service name prepended
            enriched = {'service': service, **entry}
            print(json.dumps(enriched, default=str))
            continue
        if raw_json:
            continue

        if entry is not None:
            render_structured(console, service or 'unknown', entry, no_callsite)
        else:
            render_passthrough(console, service or 'unknown', rest)


def build_filters(args: argparse.Namespace) -> Filters:
    level_rank = LEVEL_RANK.get(args.level.lower(), 0) if args.level else 0
    grep = re.compile(args.grep) if args.grep else None
    services = set(args.service) if args.service else None
    return Filters(
        level_rank=level_rank,
        module=args.module,
        request_id=args.request_id,
        event=args.event,
        grep=grep,
        services=services,
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog='log-viewer',
        description='Structured log viewer for ichrisbirch docker containers.',
    )
    p.add_argument('env', choices=['dev', 'testing', 'prod'], help='Target environment')
    p.add_argument('services', nargs='*', help='Service names to tail (e.g. api scheduler)')
    p.add_argument('--tail', type=int, default=50, help='Initial lines to show (default: 50)')
    p.add_argument('--no-follow', dest='follow', action='store_false', help='Print and exit instead of following')
    p.add_argument('--level', help='Minimum level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
    p.add_argument('--module', help='Filter by module substring (case-insensitive)')
    p.add_argument('--request-id', help='Filter to an exact X-Request-ID')
    p.add_argument('--event', help='Filter by event name substring (case-insensitive)')
    p.add_argument('--grep', help='Regex match against the full line')
    p.add_argument('--service', action='append', help='Restrict rendering to these services (repeatable)')
    p.add_argument('--no-callsite', action='store_true', help='Hide filename:line suffix on structured lines')
    p.add_argument('--json', dest='raw_json', action='store_true', help='Emit parsed JSON to stdout (for jq)')
    p.add_argument('--no-reconnect', action='store_true', help='Exit on disconnect instead of looping')
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    filters = build_filters(args)
    console = Console(highlight=False)

    signal.signal(signal.SIGINT, lambda *_: sys.exit(130))

    while True:
        cmd = build_compose_cmd(args.env, args.tail, args.follow, args.services)
        proc = stream_logs(cmd)
        try:
            process_stream(proc, console, filters, args.no_callsite, args.raw_json)
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            return 130
        finally:
            if proc.poll() is None:
                proc.terminate()

        if not args.follow or args.no_reconnect:
            return proc.returncode or 0
        time.sleep(2)


if __name__ == '__main__':
    sys.exit(main())
