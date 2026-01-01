"""Renderer for AWS infrastructure diagrams.

This module creates Graphviz diagrams for AWS infrastructure documentation.
"""

from pathlib import Path

from graphviz import Digraph

from ...utils import find_project_root


class AWSIAMDiagramRenderer:
    """Renders AWS IAM relationship diagrams."""

    def __init__(self):
        self.project_root = find_project_root()

    def _get_output_path(self, path):
        """Convert a relative path to an absolute path based on project root."""
        if path.startswith('/'):
            return path
        return str(self.project_root / path)

    def render_iam_diagram(self, output_path: str = 'docs/images/generated/aws_iam'):
        """Create a visualization of AWS IAM structure.

        Args:
            output_path: Base path for the output file (without extension)
        """
        output_path = self._get_output_path(output_path)
        dot = Digraph(comment='AWS IAM Structure')
        dot.attr(rankdir='TB')

        dot.attr('node', shape='box', style='rounded,filled', fillcolor='#E8F7FF', fontname='Arial', fontsize='12')

        with dot.subgraph(name='cluster_groups') as c:
            c.attr(label='AWS Groups', style='filled', color='#4682B4', fillcolor='#E8F7FF')
            c.node('admin', 'admin - Administrator access')
            c.node('developer', 'developer - Access to services')

        with dot.subgraph(name='cluster_policies') as c:
            c.attr(label='Policies', style='filled', color='#228B22', fillcolor='#F0FFF0')
            c.node('AWSAdministratorAccess', 'AWSAdministratorAccess')
            c.node('AllowPassRoleS3DatabaseBackups', 'AllowPassRoleS3DatabaseBackups')
            c.node('AWSKeyManagementServiceUser', 'AWSKeyManagementServiceUser')
            c.node('AmazonRDSFullAccess', 'AmazonRDSFullAccess')
            c.node('AmazonS3FullAccess', 'AmazonS3FullAccess')
            c.node('AmazonDynamoDBFullAccess', 'AmazonDynamoDBFullAccess')

        with dot.subgraph(name='cluster_roles') as c:
            c.attr(label='Roles', style='filled', color='#B22222', fillcolor='#FFF0F0')
            c.node('AWSTrustedAdvisorRole', 'AWSTrustedAdvisorRole')
            c.node('S3DatabaseBackups', 'S3DatabaseBackups - S3 Full Access')

        dot.edge('admin', 'AWSAdministratorAccess', label='Attached Policy')
        dot.edge('developer', 'AllowPassRoleS3DatabaseBackups', label='Attached Policy')
        dot.edge('developer', 'AWSKeyManagementServiceUser', label='Attached Policy')
        dot.edge('developer', 'AmazonRDSFullAccess', label='Attached Policy')
        dot.edge('developer', 'AmazonS3FullAccess', label='Attached Policy')
        dot.edge('developer', 'AmazonDynamoDBFullAccess', label='Attached Policy')

        dot.edge('AllowPassRoleS3DatabaseBackups', 'S3DatabaseBackups', label='Assume Role', style='dashed')

        dot.node(
            'AllowPassRoleS3DatabaseBackups', 'AllowPassRoleS3DatabaseBackups', style='filled', fillcolor='gray', color='#333', penwidth='2'
        )

        dot.node('S3DatabaseBackups', 'S3DatabaseBackups - S3 Full Access', style='filled', fillcolor='gray', color='#f66', penwidth='2')

        dot.render(output_path, format='svg', cleanup=True)
        return dot


def generate_aws_diagrams(output_dir: str = 'docs/images/generated'):
    """Generate all AWS-related diagrams.

    Args:
        output_dir: Directory for output files
    """
    renderer = AWSIAMDiagramRenderer()
    output_dir = renderer._get_output_path(output_dir)
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    renderer.render_iam_diagram(f'{output_dir}/aws_iam')


if __name__ == '__main__':
    generate_aws_diagrams()
