# ~/formalities/tests/utils/test_formatting_formatcode.py
import pytest
from textwrap import dedent
from formalities.utils.formatting import formatcode

def test_simple_function():
    unformatted = """
def test():
x = 1
return x"""

    expected = """def test():
    x = 1
    return x"""

    assert formatcode(dedent(unformatted).strip()) == expected

def test_nested_blocks():
    unformatted = """def outer():
x = 1
if x > 0:
y = 2
for i in range(3):
print(i)
return y"""

    expected = """def outer():
    x = 1
    if x > 0:
        y = 2
        for i in range(3):
            print(i)
        return y"""

    # Add debug output
    result = formatcode(unformatted)
    print("\nActual:")
    print(repr(result))
    print("\nExpected:")
    print(repr(expected))

    assert result == expected

def test_class_definition():
    unformatted = """
class TestClass:
def method(self):
return True"""

    expected = """class TestClass:
    def method(self):
        return True"""

    assert formatcode(dedent(unformatted).strip()) == expected

def test_mixed_control_structures():
    unformatted = """
def complex():
try:
x = 1
if x > 0:
y = 2
else:
y = 3
except:
pass"""

    expected = """def complex():
    try:
        x = 1
        if x > 0:
            y = 2
        else:
            y = 3
    except:
        pass"""

    assert formatcode(dedent(unformatted).strip()) == expected

def test_empty_lines():
    unformatted = """
def test():

x = 1

return x

"""
    expected = """def test():

    x = 1

    return x"""

    assert formatcode(dedent(unformatted).strip()) == expected

def test_invalid_syntax():
    with pytest.raises(ValueError):
        formatcode("def test() print(")

def test_multiline_strings():
    unformatted = """
def test():
x = '''
multiline
string
'''
return x"""

    expected = """def test():
    x = '''
multiline
string
'''
    return x"""

    assert formatcode(dedent(unformatted).strip()) == expected

def test_comments():
    unformatted = """
def test():
# comment
x = 1 # inline comment
return x"""

    expected = """def test():
    # comment
    x = 1 # inline comment
    return x"""

    assert formatcode(dedent(unformatted).strip()) == expected

def test_complex_nesting():
    unformatted = """
def outer():
if True:
while True:
if False:
break
else:
continue
return True"""

    expected = """def outer():
    if True:
        while True:
            if False:
                break
            else:
                continue
    return True"""

    assert formatcode(dedent(unformatted).strip()) == expected
