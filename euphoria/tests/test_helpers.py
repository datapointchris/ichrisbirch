from euphoria.tests.helpers import endpoint


def test_endpoint_int():
    assert endpoint(1) == '/1/'


def test_endpoint_float():
    assert endpoint(1.0) == '/1.0/'


def test_endpoint_str():
    assert endpoint('end') == '/end/'


def test_endpoint_list():
    assert endpoint(['endpoint', 'dir', 3, 'end']) == '/endpoint/dir/3/end/'


def test_endpoint_tuple():
    assert endpoint(('point', 'time', 4.5)) == '/point/time/4.5/'


def test_endpoint_special_char():
    assert endpoint(['$', '&', '/']) == '/$/&///'
