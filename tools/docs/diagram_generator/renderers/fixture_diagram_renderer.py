"""Renderer for creating fixture diagrams from analysis data.

This module uses Graphviz to create visualizations of test fixtures based on analysis data from the fixture analyzer.
"""

from pathlib import Path

from graphviz import Digraph

from ...utils import find_project_root
from ..analyzers.fixture_analyzer import analyze_fixtures


class FixtureDiagramRenderer:
    """Renders fixture diagrams based on analysis data."""

    def __init__(self, analysis_data: dict | None = None):
        """Initialize the renderer with analysis data.

        Args:
            analysis_data: Dictionary with fixture analysis results.
                If None, will run analyzer to get the data.
        """
        self.analysis_data = analysis_data or analyze_fixtures()
        self.colors = {
            'session': {'color': '#add8e6', 'fillcolor': '#e6f7ff'},  # Light blue
            'module': {'color': '#90ee90', 'fillcolor': '#f0fff0'},  # Light green
            'function': {'color': '#ffb6c1', 'fillcolor': '#fff0f5'},  # Light pink
            'package': {'color': '#d8bfd8', 'fillcolor': '#f5f0f5'},  # Light purple
            'class': {'color': '#ffdead', 'fillcolor': '#fff5e6'},  # Light orange
        }
        self.project_root = find_project_root()

    def _get_output_path(self, path):
        """Convert a relative path to an absolute path based on project root."""
        if path.startswith('/'):
            return path
        return str(self.project_root / path)

    def render_scope_hierarchy(self, output_path: str = 'docs/images/generated/fixture_scopes'):
        """Render a diagram showing the fixture scope hierarchy.

        Args:
            output_path: Base path for the output file (without extension)
        """
        output_path = self._get_output_path(output_path)
        dot = Digraph(comment='Pytest Fixture Scopes')
        dot.attr(rankdir='TB')

        # Define the scope hierarchy
        scopes = ['session', 'package', 'module', 'class', 'function']

        # Create nodes for each scope
        for scope in scopes:
            count = len(self.analysis_data['by_scope'].get(scope, []))
            label = f'{scope.capitalize()}\n({count} fixtures)'
            dot.node(
                scope,
                label,
                shape='box',
                style='filled',
                color=self.colors.get(scope, {}).get('color', 'black'),
                fillcolor=self.colors.get(scope, {}).get('fillcolor', 'white'),
            )

        # Connect them in the hierarchy
        for i in range(len(scopes) - 1):
            dot.edge(scopes[i], scopes[i + 1])

        # Render the diagram
        dot.render(output_path, format='svg', cleanup=True)
        return dot

    def render_fixture_dependencies(self, scope: str | None = None, output_path: str = 'docs/images/generated/fixture_dependencies'):
        """Render a diagram showing fixture dependencies.

        Args:
            scope: Optional scope to filter fixtures (session, module, etc.)
            output_path: Base path for the output file (without extension)
        """
        output_path = self._get_output_path(output_path)
        dot = Digraph(comment=f'Fixture Dependencies{f" ({scope})" if scope else ""}')
        dot.attr(rankdir='TB')

        fixtures = self.analysis_data['fixtures']
        dependencies = self.analysis_data['dependencies']

        # Filter fixtures by scope if specified
        if scope:
            fixture_names = self.analysis_data['by_scope'].get(scope, [])
            fixtures = {name: fixtures[name] for name in fixture_names if name in fixtures}
            dependencies = {name: deps for name, deps in dependencies.items() if name in fixture_names}

        # Group fixtures by category
        categories = self.analysis_data['categories']

        # Create clusters for categories
        for category, fixture_list in categories.items():
            # Filter by scope if needed
            if scope:
                fixture_list = [name for name in fixture_list if name in fixtures]

            if not fixture_list:
                continue

            with dot.subgraph(name=f'cluster_{category}') as c:
                c.attr(label=category.replace('_', ' ').title(), style='filled', color='lightgrey', fillcolor='white')

                for name in fixture_list:
                    fixture_info = fixtures.get(name, {})
                    fixture_scope = fixture_info.get('scope', 'function')

                    # Skip if not in the requested scope
                    if scope and fixture_scope != scope:
                        continue

                    # Get color based on scope
                    color_info = self.colors.get(fixture_scope, {'color': 'black', 'fillcolor': 'white'})

                    # Label with scope if not filtered by scope
                    label = name if scope else f'{name}\n({fixture_scope})'

                    # Add node
                    c.node(name, label, shape='box', style='filled', color=color_info['color'], fillcolor=color_info['fillcolor'])

        # Add edges for dependencies
        for name, deps in dependencies.items():
            if scope and fixtures.get(name, {}).get('scope') != scope:
                continue

            for dep in deps:
                if dep in fixtures and (not scope or fixtures.get(dep, {}).get('scope') == scope):
                    dot.edge(dep, name)

        # Render the diagram
        suffix = f'_{scope}' if scope else ''
        dot.render(f'{output_path}{suffix}', format='svg', cleanup=True)
        return dot

    def render_comprehensive_diagram(self, output_path: str = 'docs/images/generated/fixtures_comprehensive'):
        """Render a comprehensive diagram of all fixtures with their relationships.

        Args:
            output_path: Base path for the output file (without extension)
        """
        output_path = self._get_output_path(output_path)
        dot = Digraph(comment='Comprehensive Fixture Diagram')
        dot.attr(rankdir='TB')

        fixtures = self.analysis_data['fixtures']
        dependencies = self.analysis_data['dependencies']

        # Create scope clusters
        for scope in ('session', 'package', 'module', 'class', 'function'):
            fixture_names = self.analysis_data['by_scope'].get(scope, [])
            if not fixture_names:
                continue

            with dot.subgraph(name=f'cluster_{scope}') as c:
                color_info = self.colors.get(scope, {'color': 'black', 'fillcolor': 'white'})
                c.attr(label=f'{scope.capitalize()} Fixtures', style='filled', color=color_info['color'], fillcolor=color_info['fillcolor'])

                # Add fixtures to their scope cluster
                for name in fixture_names:
                    autouse = fixtures[name].get('autouse', False)
                    shape = 'box,bold' if autouse else 'box'
                    c.node(name, name, shape=shape)

        # Add dependency edges
        for name, deps in dependencies.items():
            for dep in deps:
                if dep in fixtures:
                    dot.edge(dep, name)

        # Render the diagram
        dot.render(output_path, format='svg', cleanup=True)
        return dot

    def render_main_fixtures_diagram(self, output_path: str = 'docs/images/generated/fixtures_diagram'):
        """Create a well-designed fixture diagram for the main documentation. This directly creates a Graphviz version instead of converting
        from Mermaid.

        Args:
            output_path: Base path for the output file (without extension)
        """
        output_path = self._get_output_path(output_path)
        dot = Digraph(comment='Test Fixtures')
        dot.attr(rankdir='TB')

        # Create main clusters
        with dot.subgraph(name='cluster_hierarchy') as c:
            c.attr(label='Fixture Scope Hierarchy', style='filled', color='lightgrey', fillcolor='#f5f5f5')
            c.node('SessionScope', 'Session Scope', shape='box')
            c.node('ModuleScope', 'Module Scope', shape='box')
            c.node('FunctionScope', 'Function Scope', shape='box')
            c.edge('SessionScope', 'ModuleScope')
            c.edge('ModuleScope', 'FunctionScope')

        with dot.subgraph(name='cluster_session') as c:
            c.attr(label='Session Fixtures', style='filled', color='#add8e6', fillcolor='#e6f7ff')
            c.node('setup_test_env', 'setup_test_environment', shape='box')
            c.node('test_env', 'TestEnvironment', shape='box')
            c.edge('setup_test_env', 'test_env')

        with dot.subgraph(name='cluster_module') as c:
            c.attr(label='Module Fixtures', style='filled', color='#90ee90', fillcolor='#f0fff0')

            # Database setup
            c.node('create_drop_tables', 'create_drop_tables', shape='box')
            c.node('insert_users_for_login', 'insert_users_for_login', shape='box')
            c.edge('create_drop_tables', 'insert_users_for_login')

            # API clients
            c.node('api_clients', 'API Client Fixtures', shape='box', style='rounded')
            c.node('test_api', 'test_api', shape='box')
            c.node('test_api_logged_in', 'test_api_logged_in', shape='box')
            c.node('test_api_logged_in_admin', 'test_api_logged_in_admin', shape='box')
            c.edge('api_clients', 'test_api', style='dotted')
            c.edge('api_clients', 'test_api_logged_in', style='dotted')
            c.edge('api_clients', 'test_api_logged_in_admin', style='dotted')

            # App clients
            c.node('app_clients', 'App Client Fixtures', shape='box', style='rounded')
            c.node('test_app', 'test_app', shape='box')
            c.node('test_app_logged_in', 'test_app_logged_in', shape='box')
            c.node('test_app_logged_in_admin', 'test_app_logged_in_admin', shape='box')
            c.edge('app_clients', 'test_app', style='dotted')
            c.edge('app_clients', 'test_app_logged_in', style='dotted')
            c.edge('app_clients', 'test_app_logged_in_admin', style='dotted')

            # Other module fixtures
            c.node('other_mod', 'Other Module Fixtures', shape='box', style='rounded')
            c.node('test_jobstore', 'test_jobstore', shape='box')
            c.edge('other_mod', 'test_jobstore', style='dotted')

        with dot.subgraph(name='cluster_function') as c:
            c.attr(label='Function Fixtures', style='filled', color='#ffb6c1', fillcolor='#fff0f5')

            # API function clients
            c.node('func_api', 'API Function Clients', shape='box', style='rounded')
            c.node('test_api_function', 'test_api_function', shape='box')
            c.node('test_api_logged_in_function', 'test_api_logged_in_function', shape='box')
            c.node('test_api_logged_in_admin_function', 'test_api_logged_in_admin_function', shape='box')
            c.edge('func_api', 'test_api_function', style='dotted')
            c.edge('func_api', 'test_api_logged_in_function', style='dotted')
            c.edge('func_api', 'test_api_logged_in_admin_function', style='dotted')

            # App function clients
            c.node('func_app', 'App Function Clients', shape='box', style='rounded')
            c.node('test_app_function', 'test_app_function', shape='box')
            c.node('test_app_logged_in_function', 'test_app_logged_in_function', shape='box')
            c.node('test_app_logged_in_admin_function', 'test_app_logged_in_admin_function', shape='box')
            c.edge('func_app', 'test_app_function', style='dotted')
            c.edge('func_app', 'test_app_logged_in_function', style='dotted')
            c.edge('func_app', 'test_app_logged_in_admin_function', style='dotted')

        with dot.subgraph(name='cluster_test_data') as c:
            c.attr(label='Test Data Fixtures', style='filled', color='#ffa500', fillcolor='#fff8dc')
            c.node('insert_testing_data', 'insert_testing_data', shape='box')
            c.node('insert_jobs_in_test_scheduler', 'insert_jobs_in_test_scheduler', shape='box')
            c.node('test_user', 'test_user', shape='box')
            c.node('test_admin_user', 'test_admin_user', shape='box')

        # Connect relationships between clusters
        dot.edge('SessionScope', 'setup_test_env', style='dashed', constraint='false')
        dot.edge('ModuleScope', 'create_drop_tables', style='dashed', constraint='false')
        dot.edge('ModuleScope', 'api_clients', style='dashed', constraint='false')
        dot.edge('ModuleScope', 'app_clients', style='dashed', constraint='false')
        dot.edge('ModuleScope', 'other_mod', style='dashed', constraint='false')
        dot.edge('FunctionScope', 'func_api', style='dashed', constraint='false')
        dot.edge('FunctionScope', 'func_app', style='dashed', constraint='false')

        # User login connections
        dot.edge('insert_users_for_login', 'test_api_logged_in')
        dot.edge('insert_users_for_login', 'test_api_logged_in_admin')
        dot.edge('insert_users_for_login', 'test_app_logged_in')
        dot.edge('insert_users_for_login', 'test_app_logged_in_admin')

        # Generate output
        dot.render(output_path, format='svg', cleanup=True)
        return dot

    def generate_all_diagrams(self, output_dir: str = 'docs/images/generated'):
        """Generate all fixture diagrams.

        Args:
            output_dir: Directory for output files
        """
        output_dir = self._get_output_path(output_dir)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        # Generate main fixtures diagram for documentation
        self.render_main_fixtures_diagram(f'{output_dir}/fixtures_diagram')

        # Generate scope hierarchy
        self.render_scope_hierarchy(f'{output_dir}/fixture_scopes')

        # Generate dependency diagrams for each scope
        for scope in ('session', 'module', 'function'):
            if scope in self.analysis_data['by_scope']:
                self.render_fixture_dependencies(scope, f'{output_dir}/fixture_dependencies')

        # Generate comprehensive diagram
        self.render_comprehensive_diagram(f'{output_dir}/fixtures_comprehensive')

        # Generate overall dependency diagram
        self.render_fixture_dependencies(output_path=f'{output_dir}/fixture_dependencies')


if __name__ == '__main__':
    renderer = FixtureDiagramRenderer()
    renderer.generate_all_diagrams()
