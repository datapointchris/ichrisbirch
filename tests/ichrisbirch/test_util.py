"""Tests for utility functions in the ichrisbirch.util module."""

import logging
from pathlib import Path
from unittest.mock import patch

from ichrisbirch.util import clean_url
from ichrisbirch.util import find_project_root
from ichrisbirch.util import get_logger_filename_from_handlername
from ichrisbirch.util import log_caller


class TestCleanUrl:
    def test_strips_utm_params(self):
        url = 'https://example.com/article?utm_source=substack&utm_medium=email&utm_campaign=post'
        assert clean_url(url) == 'https://example.com/article'

    def test_strips_mixed_tracking_params(self):
        url = 'https://laszlo.substack.com/p/async-python?utm_source=post-email-title&publication_id=61101&post_id=158726975&isFreemail=true&r=8hnll&triedRedirect=true'
        assert clean_url(url) == 'https://laszlo.substack.com/p/async-python'

    def test_preserves_non_tracking_params(self):
        url = 'https://example.com/search?q=python&page=2&utm_source=google'
        assert clean_url(url) == 'https://example.com/search?q=python&page=2'

    def test_no_params_unchanged(self):
        url = 'https://example.com/article'
        assert clean_url(url) == 'https://example.com/article'

    def test_strips_facebook_click_id(self):
        url = 'https://example.com/page?fbclid=abc123'
        assert clean_url(url) == 'https://example.com/page'

    def test_strips_fragment(self):
        url = 'https://example.com/page?utm_source=x#section'
        assert clean_url(url) == 'https://example.com/page'

    def test_case_insensitive_param_matching(self):
        url = 'https://example.com/page?UTM_SOURCE=test&title=hello'
        assert clean_url(url) == 'https://example.com/page?title=hello'

    def test_all_params_stripped_no_trailing_question_mark(self):
        url = 'https://example.com/page?utm_source=x&utm_medium=y'
        result = clean_url(url)
        assert result == 'https://example.com/page'
        assert not result.endswith('?')


class TestFindProjectRoot:
    def test_find_project_root_current_directory(self, tmp_path):
        (tmp_path / 'pyproject.toml').touch()
        result = find_project_root(directory=tmp_path)
        assert result == tmp_path.absolute()

    def test_find_project_root_parent_directory(self, tmp_path):
        nested_dir = tmp_path / 'nested' / 'directories'
        nested_dir.mkdir(parents=True)
        (tmp_path / 'pyproject.toml').touch()
        result = find_project_root(directory=nested_dir)
        assert result == tmp_path.absolute()

    def test_find_project_root_custom_target(self, tmp_path):
        nested_dir = tmp_path / 'nested'
        nested_dir.mkdir()
        (tmp_path / 'custom_file.txt').touch()
        result = find_project_root(directory=nested_dir, target_file='custom_file.txt')
        assert result == tmp_path.absolute()


class TestGetLoggerFilename:
    def test_get_logger_filename_handler_exists(self):
        handler = logging.FileHandler('test_log.txt')
        handler.name = 'test_handler'
        logging.root.handlers.append(handler)

        try:
            result = get_logger_filename_from_handlername('test_handler')
            assert result == 'test_log.txt'
        finally:
            logging.root.handlers.remove(handler)
            if Path('test_log.txt').exists():
                Path('test_log.txt').unlink()

    def test_get_logger_filename_handler_not_exists(self):
        result = get_logger_filename_from_handlername('nonexistent_handler')
        assert result is None

    def test_get_logger_filename_not_file_handler(self):
        handler = logging.StreamHandler()
        handler.name = 'stream_handler'
        logging.root.handlers.append(handler)
        try:
            result = get_logger_filename_from_handlername('stream_handler')
            assert result is None
        finally:
            logging.root.handlers.remove(handler)


class TestLogCaller:
    def test_log_caller_decorator(self):
        with patch('ichrisbirch.util.logger') as mock_logger:

            @log_caller
            def test_function():
                return 'test result'

            result = test_function()
            assert result == 'test result'
            mock_logger.info.assert_called_once()
            call_kwargs = mock_logger.info.call_args[1]
            assert call_kwargs['function'] == 'test_function'
            assert call_kwargs['caller'] == 'test_log_caller_decorator'
