from tests.helpers import format_endpoint


def test_endpoint_int():
    """Test endpoint with integer"""
    assert format_endpoint(1) == '/1/'


def test_endpoint_float():
    """Test endpoint with float"""
    assert format_endpoint(1.0) == '/1.0/'


def test_endpoint_str():
    """Test endpoint with string"""
    assert format_endpoint('end') == '/end/'


def test_endpoint_list():
    """Test endpoint with list"""
    assert format_endpoint(['endpoint', 'dir', 3, 'end']) == '/endpoint/dir/3/end/'


def test_endpoint_tuple():
    """Test endpoint with tuple"""
    assert format_endpoint(('point', 'time', 4.5)) == '/point/time/4.5/'


def test_endpoint_special_char():
    """Test endpoint with special character"""
    assert format_endpoint(['$', '&', '/']) == '/$/&///'
