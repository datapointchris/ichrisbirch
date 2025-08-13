import re
import sys
from pathlib import Path
from urllib.parse import urlparse


def find_markdown_links(content: str) -> list[tuple[str, int]]:
    """Find all markdown links in content, returning (url, line_number) tuples."""
    links = []
    lines = content.split('\n')
    link_pattern = re.compile(r'\[([^\]]*)\]\(([^)]+)\)')

    for line_num, line in enumerate(lines, start=1):
        matches = link_pattern.findall(line)
        for _, url in matches:
            links.append((url, line_num))

    return links


def is_external_link(url: str) -> bool:
    """Check if a URL is external (has a scheme like http/https)."""
    return bool(urlparse(url).scheme)


def validate_file(file_path: Path) -> list[str]:
    """Validate markdown links in a single file.

    Returns list of error messages.
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        return [f'Error reading {file_path}: {e}']

    errors = []
    links = find_markdown_links(content)

    for url, line_num in links:
        # Skip external links and anchor-only links
        if is_external_link(url) or not url or url.startswith('#'):
            continue

        # Check if it's a file link (has extension and doesn't end with /)
        if '.' in url and not url.endswith('/'):
            # Remove anchor fragments
            clean_url = url.split('#')[0]
            resolved_path = (file_path.parent / clean_url).resolve()

            if not resolved_path.exists():
                errors.append(f"{file_path}:{line_num}: broken link '{url}'")

    return errors


def main() -> int:
    """Main function for pre-commit hook usage."""
    if len(sys.argv) < 2:
        return 0

    file_paths = [Path(f) for f in sys.argv[1:] if f.endswith('.md')]
    if not file_paths:
        return 0

    all_errors = []
    for file_path in file_paths:
        errors = validate_file(file_path)
        all_errors.extend(errors)

    if all_errors:
        for error in all_errors:
            print(error)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
