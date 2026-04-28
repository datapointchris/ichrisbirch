import json
import re

from cli import log_viewer


def test_parse_prefix_strips_icb_env_prefix():
    assert log_viewer.parse_prefix('icb-dev-api       | {"event":"test"}') == ('api', '{"event":"test"}')
    assert log_viewer.parse_prefix('icb-blue-api | {"event":"x"}') == ('api', '{"event":"x"}')
    assert log_viewer.parse_prefix('icb-test-chat  | blah') == ('chat', 'blah')
    assert log_viewer.parse_prefix('icb-infra-traefik | startup') == ('traefik', 'startup')


def test_parse_prefix_handles_plain_container_name():
    assert log_viewer.parse_prefix('postgres   | starting...') == ('postgres', 'starting...')


def test_parse_prefix_returns_empty_service_for_malformed_line():
    assert log_viewer.parse_prefix('no pipe character here') == ('', 'no pipe character here')


def test_try_parse_json_accepts_structlog_line():
    line = '{"event":"task_created","level":"info","task_id":42}'
    assert log_viewer.try_parse_json(line) == {'event': 'task_created', 'level': 'info', 'task_id': 42}


def test_try_parse_json_rejects_non_json():
    assert log_viewer.try_parse_json('not json at all') is None
    assert log_viewer.try_parse_json('INFO: application startup') is None


def test_try_parse_json_rejects_json_without_event_key():
    # Traefik access logs are JSON but lack 'event' — treat as non-structlog passthrough
    assert log_viewer.try_parse_json('{"ClientAddr":"1.2.3.4","level":"info"}') is None


def test_filter_level_drops_below_threshold():
    f = log_viewer.Filters(level_rank=log_viewer.LEVEL_RANK['warning'])
    assert not log_viewer.passes_filters({'level': 'info', 'event': 'x'}, 'raw', 'api', f)
    assert log_viewer.passes_filters({'level': 'warning', 'event': 'x'}, 'raw', 'api', f)
    assert log_viewer.passes_filters({'level': 'error', 'event': 'x'}, 'raw', 'api', f)


def test_filter_request_id_requires_exact_match():
    f = log_viewer.Filters(request_id='abc123')
    assert log_viewer.passes_filters({'event': 'x', 'request_id': 'abc123'}, '', 'api', f)
    assert not log_viewer.passes_filters({'event': 'x', 'request_id': 'different'}, '', 'api', f)
    assert not log_viewer.passes_filters({'event': 'x'}, '', 'api', f)


def test_filter_module_is_case_insensitive_substring():
    f = log_viewer.Filters(module='tasks')
    assert log_viewer.passes_filters({'event': 'x', 'module': 'TasksStore'}, '', 'vue', f)
    assert log_viewer.passes_filters({'event': 'x', 'module': 'tasks_endpoints'}, '', 'api', f)
    assert not log_viewer.passes_filters({'event': 'x', 'module': 'BooksStore'}, '', 'vue', f)


def test_filter_event_is_case_insensitive_substring():
    f = log_viewer.Filters(event='auth')
    assert log_viewer.passes_filters({'event': 'auth_method_authelia'}, '', 'api', f)
    assert log_viewer.passes_filters({'event': 'AUTH_FAILED'}, '', 'api', f)
    assert not log_viewer.passes_filters({'event': 'task_created'}, '', 'api', f)


def test_filter_service_restricts_to_allowed_set():
    f = log_viewer.Filters(services={'api', 'scheduler'})
    assert log_viewer.passes_filters({'event': 'x'}, '', 'api', f)
    assert log_viewer.passes_filters({'event': 'x'}, '', 'scheduler', f)
    assert not log_viewer.passes_filters({'event': 'x'}, '', 'postgres', f)


def test_non_json_lines_pass_without_structured_filters():
    f = log_viewer.Filters()
    assert log_viewer.passes_filters(None, 'redis background save started', 'redis', f)


def test_non_json_lines_dropped_when_any_structured_filter_active():
    f = log_viewer.Filters(level_rank=log_viewer.LEVEL_RANK['warning'])
    assert not log_viewer.passes_filters(None, 'postgres auth log', 'postgres', f)


def test_grep_filter_applies_to_both_structured_and_passthrough():
    f = log_viewer.Filters(grep=re.compile('login'))
    assert log_viewer.passes_filters(None, 'user login attempt', 'api', f)
    assert log_viewer.passes_filters({'event': 'login_success'}, 'user login attempt', 'api', f)
    assert not log_viewer.passes_filters(None, 'unrelated content', 'api', f)


def test_format_val_preserves_scalars_and_json_encodes_containers():
    assert log_viewer.format_val(42) == '42'
    assert log_viewer.format_val(True) == 'true'
    assert log_viewer.format_val('simple') == 'simple'
    assert log_viewer.format_val('has spaces') == '"has spaces"'
    assert log_viewer.format_val([1, 2, 3]) == '[1, 2, 3]'
    assert log_viewer.format_val({'k': 'v'}) == '{"k": "v"}'


def test_build_compose_cmd_dev_uses_dev_overlay():
    cwd, *cmd = log_viewer.build_compose_cmd('dev', tail=50, follow=True, services=['api'])
    assert '--project-name' in cmd
    assert 'icb-dev' in cmd
    assert 'docker-compose.dev.yml' in cmd
    assert 'logs' in cmd
    assert '--tail=50' in cmd
    assert '--follow' in cmd
    assert cmd[-1] == 'api'


def test_build_compose_cmd_testing_uses_test_overlay():
    cwd, *cmd = log_viewer.build_compose_cmd('testing', tail=100, follow=False, services=[])
    assert 'icb-test' in cmd
    assert 'docker-compose.test.yml' in cmd
    assert '--follow' not in cmd


def test_build_compose_cmd_rejects_unknown_env():
    import pytest

    with pytest.raises(SystemExit):
        log_viewer.build_compose_cmd('staging', tail=50, follow=True, services=[])


def test_parse_args_collects_filters_and_services():
    args = log_viewer.parse_args(['dev', 'api', 'scheduler', '--level', 'WARNING', '--request-id', 'abc'])
    assert args.env == 'dev'
    assert args.services == ['api', 'scheduler']
    assert args.level == 'WARNING'
    assert args.request_id == 'abc'
    assert args.follow is True


def test_ansi_regex_strips_common_escape_sequences():
    colored = '\x1b[31mhello\x1b[0m world \x1b[1;34mblue\x1b[22;39m'
    assert log_viewer.ANSI_RE.sub('', colored) == 'hello world blue'


def test_round_trip_structured_to_json_passthrough():
    sample = json.dumps(
        {
            'timestamp': '2026-04-24T14:23:01Z',
            'level': 'info',
            'event': 'task_created',
            'task_id': 42,
            'request_id': 'abc',
        }
    )
    service, rest = log_viewer.parse_prefix(f'icb-dev-api | {sample}')
    entry = log_viewer.try_parse_json(rest)
    assert service == 'api'
    assert entry is not None
    assert entry['event'] == 'task_created'
    assert entry['request_id'] == 'abc'
