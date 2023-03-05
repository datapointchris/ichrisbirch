import click

from pathlib import Path

p = Path('.').resolve()

# https://github.com/tj/git-extras/blob/master/bin/git-release


@click.command()
@click.option('--version', required=True)
@click.option('--version-description', required=True)
@click.option('--dry-run', is_flag=True)
def create_release(version, version_description, dry_run):
    def print_header():
        pass

    def create_directories():
        pass

    def start_docker():
        pass

    def create_coverage_report():
        pass

    def create_lines_of_code_report():
        pass

    def create_code_complexity_report():
        pass

    def update_poetry_version():
        pass

    commands = """
        git add
        git commit

        git tag
        git push

        poetry install
    """

    def print_footer():
        pass


if __name__ == '__main__':
    create_release()
