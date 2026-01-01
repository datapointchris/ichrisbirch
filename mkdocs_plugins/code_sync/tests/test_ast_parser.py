"""Tests for the AST parser module."""

from mkdocs_plugins.code_sync.ast_parser import ASTParser
from mkdocs_plugins.code_sync.ast_parser import CodeParser
from mkdocs_plugins.code_sync.ast_parser import FallbackParser


def test_ast_parser_python_functions(python_test_file):
    """Test that the AST parser can extract Python functions."""
    parser = ASTParser()
    elements = parser.parse_file(python_test_file)

    assert 'simple_function' in elements
    assert elements['simple_function'].name == 'simple_function'
    assert 'A simple function for testing' in elements['simple_function'].code
    assert 'return' in elements['simple_function'].code


def test_ast_parser_python_classes(python_test_file):
    """Test that the AST parser can extract Python classes."""
    parser = ASTParser()
    elements = parser.parse_file(python_test_file)

    assert 'TestClass' in elements
    assert elements['TestClass'].name == 'TestClass'
    assert 'A test class with methods' in elements['TestClass'].code


def test_ast_parser_python_methods(python_test_file):
    """Test that the AST parser can extract Python class methods."""
    parser = ASTParser()
    elements = parser.parse_file(python_test_file)

    assert 'TestClass.test_method' in elements
    assert elements['TestClass.test_method'].name == 'test_method'
    assert elements['TestClass.test_method'].parent == 'TestClass'
    assert 'A test method' in elements['TestClass.test_method'].code

    assert 'TestClass.another_method' in elements
    assert elements['TestClass.another_method'].name == 'another_method'
    assert elements['TestClass.another_method'].parent == 'TestClass'
    assert 'Another test method with parameters' in elements['TestClass.another_method'].code


def test_ast_parser_python_constants(python_test_file):
    """Test that the AST parser can extract Python constants."""
    parser = ASTParser()
    elements = parser.parse_file(python_test_file)

    assert 'CONSTANT' in elements
    assert elements['CONSTANT'].name == 'CONSTANT'
    assert 'This is a constant' in elements['CONSTANT'].code


def test_fallback_parser_javascript(js_test_file):
    """Test that the fallback parser can extract JavaScript code."""
    parser = FallbackParser()
    elements = parser.parse_file(js_test_file)

    assert any('simpleFunction' in key for key in elements)
    assert any('TestClass' in key for key in elements)


def test_code_parser_delegation(python_test_file, js_test_file):
    """Test that the main CodeParser delegates to the right parser based on file type."""
    parser = CodeParser()

    python_elements = parser.parse_file(python_test_file)
    assert 'simple_function' in python_elements
    assert 'TestClass' in python_elements
    assert 'TestClass.test_method' in python_elements

    js_elements = parser.parse_file(js_test_file)
    assert len(js_elements) > 0


def test_code_element_finding(python_test_file):
    """Test that the CodeParser can find specific code elements by name."""
    parser = CodeParser()

    function = parser.find_code_element(python_test_file, 'simple_function')
    assert function is not None
    assert function.name == 'simple_function'

    method = parser.find_code_element(python_test_file, 'TestClass.test_method')
    assert method is not None
    assert method.name == 'test_method'
    assert method.parent == 'TestClass'

    method = parser.find_code_element(python_test_file, 'test_method')
    assert method is not None
    assert method.name == 'test_method'
    assert method.parent == 'TestClass'

    assert parser.find_code_element(python_test_file, 'non_existent_function') is None
