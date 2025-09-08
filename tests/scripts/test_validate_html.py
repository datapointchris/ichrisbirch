from tools.validation.validate_html import ValidateWebsite


def test_remove_multiple_subpages():
    validator = ValidateWebsite('http://testserver')
    pages = {
        'http://testserver/endpoint1/1/': '<html><body>yes</body></html>',
        'http://testserver/endpoint1/2/': '<html><body>no</body></html>',
        'http://testserver/endpoint2/1/': '<html><body>yes</body></html>',
        'http://testserver/endpoint2/2/': '<html><body>no</body></html>',
        'http://testserver/endpoint2/3/': '<html><body>no</body></html>',
        'http://testserver/end/end/2/': '<html><body>yes</body></html>',
        'http://testserver/end/end/4/': '<html><body>no</body></html>',
        'http://testserver/end/5/path/': '<html><body>yes</body></html>',
        'http://testserver/end/6/path/': '<html><body>yes</body></html>',
        'http://testserver/end/7/path/4/': '<html><body>yes</body></html>',
        'http://testserver/end/7/path/6/': '<html><body>no</body></html>',
        'http://testserver/end/6/path/8/': '<html><body>yes</body></html>',
        'http://testserver/8/9/10/': '<html><body>yes</body></html>',
        'http://testserver/8/9/11/': '<html><body>no</body></html>',
        'http://testserver/8/9/12/test/': '<html><body>yes</body></html>',
        'http://testserver/': '<html><body>yes</body></html>',
        'http://testserver/5/': '<html><body>yes</body></html>',
        'http://testserver/32/': '<html><body>no</body></html>',
    }

    yes_pages = {k for k, v in pages.items() if 'yes' in v}
    no_pages = {k for k, v in pages.items() if 'no' in v}

    deduplicated = validator.remove_multiple_subpages(pages)
    for page in yes_pages:
        assert page in deduplicated, f'{page} should not be removed'
    for page in no_pages:
        assert page not in deduplicated, f'{page} should be removed'


def test_remove_query_parameter_endpoints():
    validator = ValidateWebsite('http://testserver')
    pages = {
        'http://testserver/endpoint1/1/': '<html><body>yes</body></html>',
        'http://testserver/endpoint1/?param=okay': '<html><body>no</body></html>',
        'http://testserver/endpoint2/1/': '<html><body>yes</body></html>',
        'http://testserver/endpoint2/?param=okay': '<html><body>no</body></html>',
        'http://testserver/end/end/2/': '<html><body>yes</body></html>',
        'http://testserver/end/?q=search': '<html><body>no</body></html>',
    }

    yes_pages = {k for k, v in pages.items() if 'yes' in v}
    no_pages = {k for k, v in pages.items() if 'no' in v}

    deduplicated = validator.remove_endpoints_with_query_parameters(pages)
    for page in yes_pages:
        assert page in deduplicated, f'{page} should not be removed'
    for page in no_pages:
        assert page not in deduplicated, f'{page} should be removed'
