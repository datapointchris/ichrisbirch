from pathlib import Path

import click

p = Path().resolve()

# https://github.com/tj/git-extras/blob/master/bin/git-release


@click.command()
@click.option('--version', required=True)
@click.option('--version-description', required=True)
@click.option('--dry-run', is_flag=True)
def create_release(version, version_description, dry_run):
    """Create a release for the project"""

    def print_header():
        """Print Header"""

    def create_directories():
        """Create Directories"""

    def start_docker():
        """Start Docker"""

    def create_coverage_report():
        """Create Coverage Report"""

    def create_lines_of_code_report():
        """Create Lines of Code Report"""

    def create_code_complexity_report():
        """Create Code Complexity Report"""

    def update_poetry_version():
        """Update Poetry Version"""

    commands = """
        git add
        git commit

        git tag
        git push

        poetry install
    """

    def print_footer():
        """Print Footer"""
        print(commands)


if __name__ == '__main__':
    create_release()
