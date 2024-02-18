from ichrisbirch.app.helpers import url_builder

BASE = 'http://url.com/autotasks/'


def test_url_builder_single_string_with_leading_slash():
    assert url_builder(BASE, '/one') == 'http://url.com/autotasks/one/'


def test_url_builder_single_string_without_slash():
    assert url_builder(BASE, 'two') == 'http://url.com/autotasks/two/'


def test_url_builder_single_string_with_trailing_slash():
    assert url_builder(BASE, '/three/') == 'http://url.com/autotasks/three/'


def test_url_builder_single_string_with_slashes():
    assert url_builder(BASE, '//five') == 'http://url.com/autotasks/five/'


def test_url_builder_single_string_with_trailing_slashes():
    assert url_builder(BASE, 'six//') == 'http://url.com/autotasks/six/'


def test_url_builder_single_string_with_internal_slash():
    assert url_builder(BASE, 'seven/eight') == 'http://url.com/autotasks/seven/eight/'


def test_url_builder_single_string_with_multiple_internal_slashes():
    assert url_builder(BASE, 'nine/ten/') == 'http://url.com/autotasks/nine/ten/'


def test_url_builder_list_of_strings():
    assert url_builder(BASE, ['test', 'fifteen', 'sixteen']) == 'http://url.com/autotasks/test/fifteen/sixteen/'


def test_url_builder_list_of_strings_with_slashes():
    assert url_builder(BASE, ['/test/', '/ssss//', 'eight/']) == 'http://url.com/autotasks/test/ssss/eight/'


def test_url_builder_multiple_strings_with_slashes():
    assert url_builder(BASE, '/not/', '/in//', 'collection/') == 'http://url.com/autotasks/not/in/collection/'


def test_url_builder_single_integer():
    assert url_builder(BASE, 1) == 'http://url.com/autotasks/1/'


def test_url_builder_large_single_integer():
    assert url_builder(BASE, 458) == 'http://url.com/autotasks/458/'


def test_url_builder_multiple_integers():
    assert url_builder(BASE, 1, 2, 3) == 'http://url.com/autotasks/1/2/3/'


def test_url_builder_list_of_integers():
    assert url_builder(BASE, [4, 5, 6]) == 'http://url.com/autotasks/4/5/6/'


def test_url_builder_list_of_mixed_types():
    assert url_builder(BASE, ['four/', 5, '//six/']) == 'http://url.com/autotasks/four/5/six/'


def test_url_builder_list_of_mixed_types_empty_string():
    assert url_builder(BASE, ['four/', 5, '//six/', '']) == 'http://url.com/autotasks/four/5/six/'


def test_url_builder_list_of_mixed_types_empty_string_slashes():
    assert url_builder(BASE, ['four/', 5, '//six/', '', '/']) == 'http://url.com/autotasks/four/5/six/'


def test_url_builder_mixed_types_with_slashes():
    assert url_builder(BASE, 4, '//five//', 6, '/seven') == 'http://url.com/autotasks/4/five/6/seven/'


def test_url_builder_empty_string():
    assert url_builder(BASE, '') == 'http://url.com/autotasks/'


def test_url_builder_only_slash():
    assert url_builder(BASE, '/') == 'http://url.com/autotasks/'


def test_url_builder_slashes_empty_string():
    assert url_builder(BASE, '/abc/', '') == 'http://url.com/autotasks/abc/'


def test_url_builder_slashes_empty_string_in_middle():
    assert url_builder(BASE, '/abc/', '', '/def/') == 'http://url.com/autotasks/abc/def/'


def test_url_builder_slashes_empty_string_in_middle_many_slashes():
    assert url_builder(BASE, '/abc//', '', '//def/') == 'http://url.com/autotasks/abc/def/'
