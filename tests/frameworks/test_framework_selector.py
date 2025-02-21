# ~/formalities/tests/frameworks/test_framework_selector.py
import pytest
from formalities.utils.frameworks import (
    FrameworkSelector, FrameworkRequirement, FrameworkSuggestion
)
from formalities.core.types.propositions.atomic import AtomicProposition

def test_framework_compatibility_check(classical_framework):
    selector = FrameworkSelector()
    prop = AtomicProposition("P")

    result = selector.checkcompatibility(prop, classical_framework)
    assert result.isvalid
    assert not result.errors

def test_framework_constraints_validation(classical_framework):
    selector = FrameworkSelector()
    prop = AtomicProposition("P")

    result = selector.validateconstraints([classical_framework], prop)
    assert result.isvalid
    assert not result.errors

def test_framework_suggestions():
    selector = FrameworkSelector()
    requirements = FrameworkRequirement(
        features=["classical"],
        operators=["AND", "OR", "NOT"],
        logictypes=[]
    )

    suggestions = selector.suggest(requirements)
    assert len(suggestions) > 0
    assert all(isinstance(s, FrameworkSuggestion) for s in suggestions)
    assert all(0 <= s.compatibility <= 1 for s in suggestions)
