# ~/formalities/tests/utils/test_type_handler.py
import pytest
from formalities.utils.typesys import TypeHandler, TypeConversionResult
from formalities.core.types.propositions import (
    AtomicProposition, NumericProposition, CompoundProposition
)

def test_validate_params():
    params = {"x": 42, "y": "test"}
    expected = {"x": int, "y": str}
    errors = TypeHandler.validateparams(params, expected)
    assert len(errors) == 0

    # Missing parameter
    params = {"x": 42}
    errors = TypeHandler.validateparams(params, expected)
    assert len(errors) == 1
    assert "Missing required parameter" in errors[0]

    # Wrong type
    params = {"x": "42", "y": "test"}
    errors = TypeHandler.validateparams(params, expected)
    assert len(errors) == 1
    assert "Invalid type" in errors[0]

def test_to_prop_conversion():
    # Numeric conversion
    result = TypeHandler.toprop(42, "x")
    assert result.success
    assert isinstance(result.value, NumericProposition)
    assert result.value.value == 42

    # Boolean conversion
    result = TypeHandler.toprop(True, "p")
    assert result.success
    assert isinstance(result.value, AtomicProposition)
    assert result.value.evaluate({})

    # String conversion
    result = TypeHandler.toprop("test", "s")
    assert result.success
    assert isinstance(result.value, AtomicProposition)

    # Invalid type
    result = TypeHandler.toprop([1, 2, 3], "arr")
    assert not result.success
    assert "Cannot convert type" in result.error

def test_from_prop_conversion():
    # Numeric proposition
    num_prop = NumericProposition("x", value=42)
    result = TypeHandler.fromprop(num_prop)
    assert result.success
    assert result.value == 42

    # Atomic proposition
    atom_prop = AtomicProposition("p", _truthvalue=True)
    result = TypeHandler.fromprop(atom_prop)
    assert result.success
    assert result.value is True

    # Undefined atomic proposition
    atom_prop = AtomicProposition("p")
    result = TypeHandler.fromprop(atom_prop)
    assert result.success
    assert result.value == "p"
