"""Renderer for testing architecture diagrams.

This module creates Graphviz diagrams for the testing documentation.
"""

from pathlib import Path

from graphviz import Digraph

from ...utils import find_project_root


class TestingArchitectureDiagramRenderer:
    """Renders diagrams for the testing architecture documentation."""

    def __init__(self):
        self.project_root = find_project_root()

    def _get_output_path(self, path):
        """Convert a relative path to an absolute path based on project root."""
        if path.startswith('/'):
            return path
        return str(self.project_root / path)

    def render_testing_overview_diagram(self, output_path: str = 'docs/images/generated/testing_overview'):
        """
        Create a visualization of the overall testing architecture.

        Args:
            output_path: Base path for the output file (without extension)
        """
        output_path = self._get_output_path(output_path)
        dot = Digraph(comment='Testing Architecture')
        dot.attr(rankdir='TD')

        # Define clusters with styling
        with dot.subgraph(name='cluster_test_env') as c:
            c.attr(label='Test Environment', style='filled', color='#4682B4', fillcolor='#E8F7FF')
            c.node('TE', 'TestEnvironment Class', shape='box')
            c.node('DB', 'PostgreSQL in Docker', shape='cylinder')
            c.node('API', 'FastAPI Server', shape='box')
            c.node('APP', 'Flask Server', shape='box')
            c.edge('TE', 'DB')
            c.edge('TE', 'API')
            c.edge('TE', 'APP')

        with dot.subgraph(name='cluster_test_clients') as c:
            c.attr(label='Test Clients', style='filled', color='#228B22', fillcolor='#F0FFF0')
            c.node('TC1', 'API Test Client', shape='box')
            c.node('TC2', 'App Test Client', shape='box')
            c.edge('TC1', 'API')
            c.edge('TC2', 'APP')

        with dot.subgraph(name='cluster_test_data') as c:
            c.attr(label='Test Data', style='filled', color='#B22222', fillcolor='#FFF0F0')
            c.node('TD', 'Test Data Modules', shape='box')
            c.edge('TD', 'DB')

        with dot.subgraph(name='cluster_fixtures') as c:
            c.attr(label='Fixtures', style='filled', color='#9932CC', fillcolor='#F8F0FF')
            c.node('F1', 'Session Fixtures', shape='box')
            c.node('F2', 'Module Fixtures', shape='box')
            c.node('F3', 'Function Fixtures', shape='box')
            c.edge('F1', 'TE')
            c.edge('F2', 'TD')
            c.edge('F3', 'TC1')
            c.edge('F3', 'TC2')

        with dot.subgraph(name='cluster_tests') as c:
            c.attr(label='Tests', style='filled', color='#FF8C00', fillcolor='#FFF8E8')
            c.node('T1', 'API Tests', shape='box')
            c.node('T2', 'App Tests', shape='box')
            c.node('T3', 'Integration Tests', shape='box')
            c.edge('T1', 'TC1')
            c.edge('T2', 'TC2')
            c.edge('T3', 'TC1')
            c.edge('T3', 'TC2')

        # Generate output
        dot.render(output_path, format='svg', cleanup=True)
        return dot

    def render_environment_architecture_diagram(self, output_path: str = 'docs/images/generated/test_env_architecture'):
        """
        Create a visualization of the test environment architecture.

        Args:
            output_path: Base path for the output file (without extension)
        """
        output_path = self._get_output_path(output_path)
        dot = Digraph(comment='Test Environment Architecture')
        dot.attr(rankdir='TD')

        with dot.subgraph(name='cluster_test_session') as c:
            c.attr(label='Test Session', style='filled', color='#4682B4', fillcolor='#E8F7FF')
            c.node('TE', 'TestEnvironment Class', shape='box')

        with dot.subgraph(name='cluster_infrastructure') as c:
            c.attr(label='Infrastructure', style='filled', color='#228B22', fillcolor='#F0FFF0')
            c.node('DB', 'PostgreSQL in Docker', shape='cylinder')
            c.node('API', 'FastAPI Server', shape='box')
            c.node('APP', 'Flask Server', shape='box')

        with dot.subgraph(name='cluster_test_execution') as c:
            c.attr(label='Test Execution', style='filled', color='#B22222', fillcolor='#FFF0F0')
            c.node('TS', 'Test Setup', shape='box')
            c.node('TT', 'Test Teardown', shape='box')
            c.node('TR', 'Test Running', shape='box')

        # Connect components
        dot.edge('TE', 'DB', label='Creates')
        dot.edge('TE', 'API', label='Starts')
        dot.edge('TE', 'APP', label='Starts')

        dot.edge('TS', 'TE', label='Uses')
        dot.edge('TT', 'TE', label='Cleans up')
        dot.edge('TR', 'API', label='Interacts with')
        dot.edge('TR', 'APP', label='Interacts with')
        dot.edge('TR', 'DB', label='Queries')

        # Generate output
        dot.render(output_path, format='svg', cleanup=True)
        return dot

    def render_environment_setup_sequence(self, output_path: str = 'docs/images/generated/test_env_setup_sequence'):
        """
        Create a sequence diagram of the test environment setup process.

        Args:
            output_path: Base path for the output file (without extension)
        """
        output_path = self._get_output_path(output_path)
        # For sequence diagrams, we'll use a different approach in Graphviz
        dot = Digraph(comment='Test Environment Setup Sequence')
        dot.attr(rankdir='LR')  # Left to right for sequence diagrams

        # Define participants
        participants = [
            ('PyTest', 'PyTest'),
            ('TE', 'TestEnvironment'),
            ('Docker', 'Docker'),
            ('DB', 'PostgreSQL'),
            ('API', 'FastAPI Server'),
            ('APP', 'Flask Server'),
        ]

        # Create participant nodes
        for id, label in participants:
            dot.node(id, label, shape='box')

        # Invisible edges to enforce order
        for i in range(len(participants) - 1):
            dot.edge(participants[i][0], participants[i + 1][0], style='invis')

        # Create the sequence diagram with edges and labels
        dot.attr('edge', constraint='false', fontsize='10')

        # Define sequence with edge styling
        edge_style = {
            'request': {'color': 'blue', 'dir': 'forward', 'arrowhead': 'vee'},
            'response': {'color': 'green', 'dir': 'back', 'arrowhead': 'vee', 'style': 'dashed'},
        }

        # Setup sequence
        self._add_sequence_edge(dot, 'PyTest', 'TE', 'setup_test_environment fixture', **edge_style['request'])
        self._add_sequence_edge(dot, 'TE', 'Docker', 'Create PostgreSQL container', **edge_style['request'])
        self._add_sequence_edge(dot, 'Docker', 'TE', 'Container created', **edge_style['response'])
        self._add_sequence_edge(dot, 'TE', 'Docker', 'Start container', **edge_style['request'])
        self._add_sequence_edge(dot, 'Docker', 'DB', 'Start PostgreSQL', **edge_style['request'])
        self._add_sequence_edge(dot, 'DB', 'Docker', 'Started', **edge_style['response'])
        self._add_sequence_edge(dot, 'TE', 'DB', 'Create database schemas', **edge_style['request'])
        self._add_sequence_edge(dot, 'DB', 'TE', 'Schemas created', **edge_style['response'])
        self._add_sequence_edge(dot, 'TE', 'API', 'Start FastAPI server', **edge_style['request'])
        self._add_sequence_edge(dot, 'API', 'TE', 'Server started', **edge_style['response'])
        self._add_sequence_edge(dot, 'TE', 'APP', 'Start Flask server', **edge_style['request'])
        self._add_sequence_edge(dot, 'APP', 'TE', 'Server started', **edge_style['response'])
        self._add_sequence_edge(dot, 'TE', 'PyTest', 'Environment ready', **edge_style['response'])

        # Generate output
        dot.render(output_path, format='svg', cleanup=True)
        return dot

    def render_environment_teardown_sequence(self, output_path: str = 'docs/images/generated/test_env_teardown_sequence'):
        """
        Create a sequence diagram of the test environment teardown process.

        Args:
            output_path: Base path for the output file (without extension)
        """
        output_path = self._get_output_path(output_path)
        dot = Digraph(comment='Test Environment Teardown Sequence')
        dot.attr(rankdir='LR')  # Left to right for sequence diagrams

        # Define participants
        participants = [
            ('PyTest', 'PyTest'),
            ('TE', 'TestEnvironment'),
            ('Docker', 'Docker'),
            ('DB', 'PostgreSQL'),
            ('API', 'FastAPI Server'),
            ('APP', 'Flask Server'),
        ]

        # Create participant nodes
        for id, label in participants:
            dot.node(id, label, shape='box')

        # Invisible edges to enforce order
        for i in range(len(participants) - 1):
            dot.edge(participants[i][0], participants[i + 1][0], style='invis')

        # Create the sequence diagram with edges and labels
        dot.attr('edge', constraint='false', fontsize='10')

        # Define sequence with edge styling
        edge_style = {
            'request': {'color': 'blue', 'dir': 'forward', 'arrowhead': 'vee'},
            'response': {'color': 'green', 'dir': 'back', 'arrowhead': 'vee', 'style': 'dashed'},
        }

        # Teardown sequence
        self._add_sequence_edge(dot, 'PyTest', 'TE', 'Teardown test environment', **edge_style['request'])
        self._add_sequence_edge(dot, 'TE', 'Docker', 'Stop PostgreSQL container', **edge_style['request'])
        self._add_sequence_edge(dot, 'Docker', 'DB', 'Stop PostgreSQL', **edge_style['request'])
        self._add_sequence_edge(dot, 'DB', 'Docker', 'Stopped', **edge_style['response'])
        self._add_sequence_edge(dot, 'TE', 'API', 'Kill FastAPI server process', **edge_style['request'])
        self._add_sequence_edge(dot, 'API', 'TE', 'Process terminated', **edge_style['response'])
        self._add_sequence_edge(dot, 'TE', 'APP', 'Kill Flask server process', **edge_style['request'])
        self._add_sequence_edge(dot, 'APP', 'TE', 'Process terminated', **edge_style['response'])
        self._add_sequence_edge(dot, 'TE', 'PyTest', 'Environment cleaned up', **edge_style['response'])

        # Generate output
        dot.render(output_path, format='svg', cleanup=True)
        return dot

    def render_test_writing_workflow_diagram(self, output_path: str = 'docs/images/generated/test_writing_workflow'):
        """
        Create a visualization of the test writing workflow.

        Args:
            output_path: Base path for the output file (without extension)
        """
        output_path = self._get_output_path(output_path)
        dot = Digraph(comment='Test Writing Workflow')
        dot.attr(rankdir='TB')

        # Styling
        dot.attr('node', shape='box', style='rounded,filled', fillcolor='#E8F7FF', fontname='Arial', fontsize='12')

        # Main workflow nodes
        dot.node('req', 'Define Requirements', fillcolor='#FFF0F0')
        dot.node('setup', 'Set Up Test Environment', fillcolor='#F0FFF0')
        dot.node('fixtures', 'Choose/Create Fixtures', fillcolor='#F0F0FF')
        dot.node('data', 'Prepare Test Data', fillcolor='#FFF8E8')
        dot.node('write', 'Write Test Case', fillcolor='#F5F5F5')
        dot.node('run', 'Run Test', fillcolor='#E6F7FF')
        dot.node('refine', 'Refine Test', fillcolor='#F0FFF0')

        # Edge connections
        dot.edge('req', 'setup')
        dot.edge('setup', 'fixtures')
        dot.edge('fixtures', 'data')
        dot.edge('data', 'write')
        dot.edge('write', 'run')
        dot.edge('run', 'refine')
        dot.edge('refine', 'run', label='Iterate')

        # Self-explanatory notes
        dot.node('note1', 'Use conftest.py\nfor shared fixtures', shape='note', fillcolor='#FFFACD')
        dot.node('note2', 'Consider test isolation\nand performance', shape='note', fillcolor='#FFFACD')
        dot.node('note3', 'Use test data factories\nfor consistent data', shape='note', fillcolor='#FFFACD')

        # Connect notes
        dot.edge('note1', 'fixtures', style='dashed', arrowhead='none')
        dot.edge('note2', 'setup', style='dashed', arrowhead='none')
        dot.edge('note3', 'data', style='dashed', arrowhead='none')

        # Generate output
        dot.render(output_path, format='svg', cleanup=True)
        return dot

    def _add_sequence_edge(self, graph, source, target, label, **attrs):
        """Helper method to add a sequence diagram edge with proper attributes."""
        graph.edge(source, target, label=label, **attrs)


def generate_testing_diagrams(output_dir: str = 'docs/images/generated'):
    """
    Generate all testing-related diagrams.

    Args:
        output_dir: Directory for output files
    """
    renderer = TestingArchitectureDiagramRenderer()
    output_dir = renderer._get_output_path(output_dir)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Generate testing diagrams
    renderer.render_testing_overview_diagram(f'{output_dir}/testing_overview')
    renderer.render_environment_architecture_diagram(f'{output_dir}/test_env_architecture')
    renderer.render_environment_setup_sequence(f'{output_dir}/test_env_setup_sequence')
    renderer.render_environment_teardown_sequence(f'{output_dir}/test_env_teardown_sequence')
    renderer.render_test_writing_workflow_diagram(f'{output_dir}/test_writing_workflow')


if __name__ == '__main__':
    generate_testing_diagrams()
