"""Tests for utility functions in the ichrisbirch.util module."""

import logging
from pathlib import Path
from unittest.mock import patch

from ichrisbirch.util import find_project_root
from ichrisbirch.util import get_logger_filename_from_handlername
from ichrisbirch.util import log_caller


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
        with patch('logging.Logger.info') as mock_log:

            @log_caller
            def test_function():
                return 'test result'

            result = test_function()
            assert result == 'test result'
            mock_log.assert_called_once()
            log_message = mock_log.call_args[0][0]
            assert "function 'test_function' was called by" in log_message
