# ~/formalities/tests/validation/test_context.py
import pytest
from formalities.validation.base import ValidationContext, FrameworkContext
from formalities.core.types.propositions.atomic import AtomicProposition

def test_validation_context_creation(classical_framework):
    context = ValidationContext(framework=classical_framework)
    assert context.framework is not None
    assert isinstance(context.options, dict)
    assert isinstance(context.metadata, dict)
    assert isinstance(context.history, list)

def test_validation_context_recording(classical_framework):
    context = ValidationContext(framework=classical_framework)
    prop = AtomicProposition("P")

    context.record(
        source="test",
        proposition=prop,
        success=True,
        errors=None
    )

    assert len(context.history) == 1
    record = context.history[0]
    assert record["source"] == "test"
    assert record["proposition"] == str(prop)
    assert record["success"] is True
    assert record["errors"] == []

def test_validation_context_child_creation(classical_framework):
    parent = ValidationContext(
        framework=classical_framework,
        options={"test": True},
        metadata={"meta": "data"}
    )

    child = parent.createchild()

    assert child.framework == parent.framework
    assert child.options == parent.options
    assert child.metadata == parent.metadata
    assert child.history == parent.history

    # Verify child modifications don't affect parent
    child.options["new"] = True
    assert "new" not in parent.options
