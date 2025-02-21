# ~/formalities/tests/conftest.py
import pytest
from pathlib import Path
import sys

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Common fixtures
@pytest.fixture
def sample_atomic_prop():
    from formalities.core.types.propositions.atomic import AtomicProposition
    return AtomicProposition("P", _truthvalue=True)

@pytest.fixture
def sample_numeric_prop():
    from formalities.core.types.propositions.numeric import NumericProposition
    return NumericProposition("x", value=42)

@pytest.fixture
def sample_compound_prop():
    from formalities.core.types.propositions.atomic import AtomicProposition
    from formalities.core.types.propositions.compound import CompoundProposition
    from formalities.core.types.operators.boolean import AND
    p = AtomicProposition("P", _truthvalue=True)
    q = AtomicProposition("Q", _truthvalue=False)
    return CompoundProposition(AND(), (p, q))

@pytest.fixture
def classical_framework():
    from formalities.frameworks.simple import ClassicalFramework
    return ClassicalFramework()

@pytest.fixture
def validation_context(classical_framework):
    from formalities.validation.base import ValidationContext
    return ValidationContext(framework=classical_framework)
