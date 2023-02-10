from tests.helpers import endpoint


def test_endpoint_int():
    """Test endpoint with integer"""
    assert endpoint(1) == '/1/'


def test_endpoint_float():
    """Test endpoint with float"""
    assert endpoint(1.0) == '/1.0/'


def test_endpoint_str():
    """Test endpoint with string"""
    assert endpoint('end') == '/end/'


def test_endpoint_list():
    """Test endpoint with list"""
    assert endpoint(['endpoint', 'dir', 3, 'end']) == '/endpoint/dir/3/end/'


def test_endpoint_tuple():
    """Test endpoint with tuple"""
    assert endpoint(('point', 'time', 4.5)) == '/point/time/4.5/'


def test_endpoint_special_char():
    """Test endpoint with special character"""
    assert endpoint(['$', '&', '/']) == '/$/&///'
