"""Verify all JavaScript fetch() POST calls include CSRF tokens.

Templates that use fetch() to make POST requests must include the X-CSRFToken header,
otherwise the request will be rejected by Flask-WTF's CSRF protection in production.
The test client disables CSRF (WTF_CSRF_ENABLED=False), so this is the only way to
catch missing tokens before they break in production.
"""

from pathlib import Path

TEMPLATES_DIR = Path('ichrisbirch/app/templates')


def find_templates_with_fetch_post():
    """Find all templates that make fetch() POST requests."""
    results = []
    for template in TEMPLATES_DIR.rglob('*.html'):
        content = template.read_text()
        if 'fetch(' in content and 'method:' in content and "'POST'" in content:
            results.append(template)
    return results


def test_all_fetch_posts_include_csrf_token():
    """Every template with a fetch() POST must include X-CSRFToken in headers."""
    templates = find_templates_with_fetch_post()
    assert templates, f'Expected to find templates with fetch() POST calls in {TEMPLATES_DIR}'

    missing = []
    for template in templates:
        content = template.read_text()
        if 'X-CSRFToken' not in content:
            missing.append(str(template.relative_to(TEMPLATES_DIR)))

    assert not missing, (
        f'Templates with fetch() POST missing X-CSRFToken header: {", ".join(missing)}. '
        f'Add the CSRF token to the fetch headers: '
        f'const csrfToken = document.querySelector(\'input[name="csrf_token"]\').value; '
        f"then include 'X-CSRFToken': csrfToken in the headers."
    )
