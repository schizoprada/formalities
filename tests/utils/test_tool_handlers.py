# ~/formalities/tests/utils/test_tool_handlers.py
import pytest
from formalities.utils.toolcalls import (
    ToolCallHandler, ToolCallRequest, ToolCallResponse,
    toolcallhandler
)
from formalities.utils.discovery import frameworkregistry, ComponentInfo
from formalities.core.types.propositions import AtomicProposition
from formalities.validation.strategies.logicalconsistency import LogicalConsistencyStrategy
from formalities.validation.strategies.syntactic import SyntacticValidationStrategy

# Helper functions for tests
def get_component_types(response):
    """Extract all unique component types from a matchmaker response"""
    if not response.success or not response.data or "available" not in response.data:
        return set()
    return {comp["type"] for comp in response.data["available"]}

def is_success_with_result(response):
    """Check if a methodbuilder response is successful and contains a result"""
    return (response.success and
            response.data is not None and
            "result" in response.data)


@pytest.fixture(autouse=True)
def register_validation_strategies():
    # Clear any existing registrations first
    if hasattr(frameworkregistry, '_components'):
        existing = dict(frameworkregistry._components)
    else:
        existing = {}

    # Force register our validation strategies
    frameworkregistry._components.update({
        "LogicalConsistencyStrategy": ComponentInfo(
            name="LogicalConsistencyStrategy",
            typeof="validator",
            description="Validates logical consistency of propositions",
            modulepath="formalities.validation.strategies.logicalconsistency",
            classname="LogicalConsistencyStrategy"
        ),
        "SyntacticValidationStrategy": ComponentInfo(
            name="SyntacticValidationStrategy",
            typeof="validator",
            description="Validates syntactic correctness of propositions",
            modulepath="formalities.validation.strategies.syntactic",
            classname="SyntacticValidationStrategy"
        )
    })

    yield

    # Restore original state
    frameworkregistry._components = existing

# Matchmaker Tests
def test_matchmaker_basic_discovery():
    request = ToolCallRequest(
        tool="matchmaker",
        query={"task": "validate", "needs": ["classical"]}
    )

    response = toolcallhandler._matchmaker(request.query)
    assert response.success
    assert response.data is not None
    assert "available" in response.data
    assert len(response.data["available"]) > 0

    # Should find ClassicalFramework
    found_classical = False
    for comp in response.data["available"]:
        if comp["name"] == "ClassicalFramework":
            found_classical = True
            assert comp["type"] == "framework"
            break
    assert found_classical

def test_matchmaker_multiple_needs():
    # First verify our registry state
    validators = [c for c in frameworkregistry._components.values() if c.typeof == "validator"]
    assert len(validators) > 0, "No validators registered before test"

    request = ToolCallRequest(
        tool="matchmaker",
        query={"task": "analyze", "needs": ["validation", "logic"]}
    )

    response = toolcallhandler._matchmaker(request.query)
    assert response.success
    assert response.data is not None

    found_types = get_component_types(response)
    assert "validator" in found_types, f"Expected validator type in {found_types}"
    assert "framework" in found_types, f"Expected framework type in {found_types}"

def test_matchmaker_empty_query():
    request = ToolCallRequest(
        tool="matchmaker",
        query={}
    )

    response = toolcallhandler._matchmaker(request.query)
    assert response.success
    assert response.data is not None
    assert len(response.data["available"]) > 0  # Should return all available components

# Methodbuilder Tests
def test_methodbuilder_simple_execution():
    code = """
def main():
    from formalities.core.types.propositions.atomic import AtomicProposition
    return AtomicProposition("P", _truthvalue=True)
"""
    request = ToolCallRequest(
        tool="methodbuilder",
        query={
            "code": code,
            "frameworks": ["ClassicalFramework"],
            "validators": ["LogicalConsistencyStrategy"],
            "args": {}
        }
    )

    response = toolcallhandler._methodbuilder(request.query)
    assert response.success
    assert response.data is not None
    assert "result" in response.data
    assert isinstance(response.data["result"], AtomicProposition)
    assert response.data["result"].evaluate({})  # Should be True

def test_methodbuilder_with_validation_failure():
    # Create code that will fail validation
    code = """
def main():
    from formalities.core.types.propositions.atomic import AtomicProposition
    p = AtomicProposition("P")  # No truth value set
    return p
"""
    request = ToolCallRequest(
        tool="methodbuilder",
        query={
            "code": code,
            "frameworks": ["ClassicalFramework"],
            "validators": ["LogicalConsistencyStrategy"],
            "args": {}
        }
    )

    response = toolcallhandler._methodbuilder(request.query)
    assert not response.success
    assert response.error is not None
    assert "Evaluation Error" in response.error

def test_methodbuilder_with_args():
    code = """
def main(value: bool = False):
    from formalities.core.types.propositions.atomic import AtomicProposition
    return AtomicProposition("P", _truthvalue=value)
"""
    request = ToolCallRequest(
        tool="methodbuilder",
        query={
            "code": code,
            "frameworks": ["ClassicalFramework"],
            "validators": ["LogicalConsistencyStrategy"],
            "args": {"value": True}
        }
    )

    response = toolcallhandler._methodbuilder(request.query)
    assert response.success
    assert response.data is not None
    assert response.data["result"].evaluate({})  # Should be True

def test_methodbuilder_syntax_error():
    code = """
def main():
    syntax error here
    return None
"""
    request = ToolCallRequest(
        tool="methodbuilder",
        query={
            "code": code,
            "frameworks": ["ClassicalFramework"],
            "args": {}
        }
    )

    response = toolcallhandler._methodbuilder(request.query)
    assert not response.success
    assert response.error is not None
    assert "syntax" in response.error.lower()

def test_methodbuilder_invalid_frameworks():
    code = """
def main():
    from formalities.core.types.propositions.atomic import AtomicProposition
    return AtomicProposition("P", _truthvalue=True)
"""
    request = ToolCallRequest(
        tool="methodbuilder",
        query={
            "code": code,
            "frameworks": ["NonExistentFramework"],
            "args": {}
        }
    )

    response = toolcallhandler._methodbuilder(request.query)
    assert not response.success
    assert response.error is not None

def test_methodbuilder_multiple_validators():
    code = """
def main():
    from formalities.core.types.propositions.atomic import AtomicProposition
    return AtomicProposition("P", _truthvalue=True)
"""
    request = ToolCallRequest(
        tool="methodbuilder",
        query={
            "code": code,
            "frameworks": ["ClassicalFramework"],
            "validators": ["LogicalConsistencyStrategy", "SyntacticValidationStrategy"],
            "args": {}
        }
    )

    response = toolcallhandler._methodbuilder(request.query)
    assert response.success
    assert response.data is not None
    assert "validation" in response.data
    assert "history" in response.data["validation"]

    # Should have validation history from both strategies
    validation_sources = set()
    for record in response.data["validation"]["history"]:
        validation_sources.add(record["source"])

    assert "strategy:LogicalConsistencyStrategy" in validation_sources
    assert "strategy:SyntacticValidationStrategy" in validation_sources
