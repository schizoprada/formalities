# ~/formalities/tests/core/types/test_numeric_propositions.py
import pytest
from formalities.core.types.propositions.numeric import NumericProposition

def test_numeric_prop_creation():
    prop = NumericProposition("x", value=42)
    assert prop.symbol == "x"
    assert prop.value == 42
    assert prop.evaluate({})  # Should be True since value exists

def test_numeric_prop_arithmetic():
    x = NumericProposition("x", value=10)
    y = NumericProposition("y", value=5)

    sum_prop = x + y
    assert sum_prop.value == 15

    diff_prop = x - y
    assert diff_prop.value == 5

    prod_prop = x * y
    assert prod_prop.value == 50

def test_numeric_prop_comparisons():
    x = NumericProposition("x", value=10)
    y = NumericProposition("y", value=5)

    assert x > y
    assert y < x
    assert x >= y
    assert y <= x
    assert not (x == y)

def test_numeric_prop_undefined():
    prop = NumericProposition("x")
    assert prop.value is None
    assert not prop.evaluate({})

    with pytest.raises(ValueError):
        prop + NumericProposition("y", value=5)
