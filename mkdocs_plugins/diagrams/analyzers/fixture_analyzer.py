"""Analyzer for test fixtures in the project.

This module analyzes the actual test fixtures in the project's codebase and generates data structures that can be used to create diagrams.
"""

import ast
import os
from pathlib import Path

from ...utils import find_project_root


class FixtureVisitor(ast.NodeVisitor):
    """AST visitor that extracts pytest fixture information."""

    def __init__(self):
        self.fixtures = {}
        self.current_fixture = None

    def visit_FunctionDef(self, node):
        """Visit function definition nodes to find fixtures."""
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name) and decorator.func.id == 'pytest.fixture':
                scope = 'function'
                autouse = False

                for keyword in decorator.keywords:
                    if keyword.arg == 'scope' and isinstance(keyword.value, ast.Constant):
                        scope = keyword.value.value
                    elif keyword.arg == 'autouse' and isinstance(keyword.value, ast.Constant):
                        autouse = keyword.value.value

                self.current_fixture = node.name
                self.fixtures[node.name] = {
                    'name': node.name,
                    'scope': scope,
                    'autouse': autouse,
                    'dependencies': [],
                    'docstring': ast.get_docstring(node) or '',
                    'code': None,
                }

                for arg in node.args.args:
                    if arg.arg != 'self' and arg.arg != 'cls':
                        self.fixtures[node.name]['dependencies'].append(arg.arg)

        self.generic_visit(node)
        self.current_fixture = None


def analyze_fixtures_in_file(file_path: str | Path) -> dict:
    """Analyze fixtures in a Python file using AST.

    Args:
        file_path: Path to the Python file

    Returns:
        Dictionary of fixtures found in the file
    """
    try:
        file_content = Path(file_path).read_text()

        tree = ast.parse(file_content)
        visitor = FixtureVisitor()
        visitor.visit(tree)
        return visitor.fixtures
    except Exception as e:
        print(f'Error analyzing {file_path}: {e}')
        return {}


def analyze_fixtures_in_directory(dir_path: str) -> dict:
    """Recursively analyze fixtures in all Python files in a directory.

    Args:
        dir_path: Path to the directory

    Returns:
        Dictionary of all fixtures found
    """
    all_fixtures = {}

    for root, _dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                fixtures = analyze_fixtures_in_file(file_path)
                all_fixtures.update(fixtures)

    return all_fixtures


def group_fixtures_by_scope(fixtures: dict) -> dict[str, list[str]]:
    """Group fixtures by their scope.

    Args:
        fixtures: Dictionary of fixtures

    Returns:
        Dictionary mapping scopes to lists of fixture names
    """
    scopes: dict[str, list[str]] = {}

    for name, fixture in fixtures.items():
        scope = fixture['scope']
        if scope not in scopes:
            scopes[scope] = []
        scopes[scope].append(name)

    return scopes


def get_fixture_dependencies(fixtures: dict) -> dict[str, set[str]]:
    """Extract fixture dependencies.

    Args:
        fixtures: Dictionary of fixtures

    Returns:
        Dictionary mapping fixture names to sets of dependency names
    """
    dependencies = {}

    for name, fixture in fixtures.items():
        dependencies[name] = set(fixture['dependencies'])

    return dependencies


def analyze_fixture_categories(fixtures: dict) -> dict[str, list[str]]:
    """Categorize fixtures based on naming patterns or usage.

    Args:
        fixtures: Dictionary of fixtures

    Returns:
        Dictionary mapping categories to lists of fixture names
    """
    categories: dict[str, list[str]] = {'api_clients': [], 'app_clients': [], 'database': [], 'test_data': [], 'other': []}

    for name in fixtures:
        if 'api' in name.lower() and 'client' in name.lower():
            categories['api_clients'].append(name)
        elif 'app' in name.lower() and 'client' in name.lower():
            categories['app_clients'].append(name)
        elif any(db_term in name.lower() for db_term in ('db', 'database', 'table', 'session')):
            categories['database'].append(name)
        elif any(data_term in name.lower() for data_term in ('data', 'test_data', 'insert')):
            categories['test_data'].append(name)
        else:
            categories['other'].append(name)

    return categories


def analyze_fixtures() -> dict:
    """Analyze all fixtures in the project.

    Returns:
        Dictionary with fixture analysis results
    """
    project_root = find_project_root()
    tests_dir = project_root / 'tests'

    fixtures = analyze_fixtures_in_directory(str(tests_dir))

    result = {
        'fixtures': fixtures,
        'by_scope': group_fixtures_by_scope(fixtures),
        'dependencies': get_fixture_dependencies(fixtures),
        'categories': analyze_fixture_categories(fixtures),
    }

    return result


if __name__ == '__main__':
    analysis = analyze_fixtures()
    print(f'Found {len(analysis["fixtures"])} fixtures')
    print(f'Scopes: {list(analysis["by_scope"].keys())}')
    for scope, fixtures in analysis['by_scope'].items():
        print(f'- {scope}: {len(fixtures)} fixtures')

    for category, fixtures in analysis['categories'].items():
        print(f'{category}: {len(fixtures)} fixtures')
