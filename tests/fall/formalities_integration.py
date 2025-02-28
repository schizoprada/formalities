# ~/formalities/tests/fall/formalities_integration.py
import pytest
from formalities.fall.bridges.adapter import FormalitiesAdapter
from formalities.fall.bridges.nlp import NLPBridge
from formalities.core.types.propositions import (
    AtomicProposition, CompoundProposition, Proposition
)
from formalities.core.types.evaluations import EvaluationContext, EvaluationMode
from formalities.core.types.operators.boolean import (
    AND, OR, NOT, IMPLIES, IFF, ANDN
)
from formalities.validation.base import Validator, ValidationContext, ValidationResult, ValidationStrategy, ValidationType
from formalities.frameworks.simple import ClassicalFramework
from formalities.validation.strategies.logicalconsistency import LogicalConsistencyStrategy
from formalities.validation.strategies.syntactic import SyntacticValidationStrategy
from loguru import logger as log

class LogicalConsistencyStrategy(ValidationStrategy):
    @property
    def validationtype(self) -> ValidationType:
        return ValidationType.LOGICAL

    def validate(self, proposition: Proposition, context: ValidationContext) -> ValidationResult:
        errors = []
        try:
            # Determine which evaluation mode to use based on context options
            if 'evaluation_mode' in context.options:
                mode_str = context.options['evaluation_mode']
                if mode_str == 'structural':
                    mode = EvaluationMode.STRUCTURAL
                elif mode_str == 'semantic':
                    mode = EvaluationMode.SEMANTIC
                else:
                    mode = EvaluationMode.STRICT
            else:
                # Default to structural for backward compatibility
                mode = EvaluationMode.STRUCTURAL

            # Create evaluation context with appropriate mode
            eval_context = EvaluationContext(context.options, mode=mode)

            # Evaluate the proposition
            result = eval_context.evaluate(proposition)

            # Get feedback for validation
            feedback = eval_context.validationfeedback

            log.debug(f"logicalconsistencystrategy.validate | evaluation result: {result}")
            log.debug(f"logicalconsistencystrategy.validate | feedback: {feedback}")

            # If structure is valid according to chosen mode, return success
            if feedback['validstructure']:
                return ValidationResult(True, [])
            else:
                missing = ', '.join(feedback['missingvalues'])
                errors.append(f"Invalid structure: missing values for {missing}")

        except Exception as e:
            log.debug(f"logicalconsistencystrategy.validate | evaluation error: {str(e)}")
            errors.append(f"Evaluation Error: {str(e)}")

        return ValidationResult(
            (len(errors)==0),
            errors
        )

class TestFormalitiesAdapter:
    def setup_method(self):
        # Set up adapter and framework
        self.adapter = FormalitiesAdapter()
        self.framework = ClassicalFramework()
        self.validator = Validator(self.framework)
        self.validator.addstrategy(SyntacticValidationStrategy())

        # Use our adapted strategy instead
        self.validator.addstrategy(LogicalConsistencyStrategy())

    def test_create_proposition(self):
        # Test creating proposition with no truth value
        prop = self.adapter.createproposition("p")
        assert prop.symbol == "p"
        assert prop._truthvalue is None

        # Test creating proposition with truth value
        true_prop = self.adapter.createproposition("q", True)
        assert true_prop.symbol == "q"
        assert true_prop._truthvalue is True
        assert true_prop.evaluate() is True

        # Test proposition gets stored in adapter's registry
        assert self.adapter.getproposition("p") is prop
        assert self.adapter.getproposition("q") is true_prop

    def test_create_compound(self):
        # Create atomic propositions
        p = self.adapter.createproposition("p", True)
        q = self.adapter.createproposition("q", False)

        # Test AND
        and_prop = self.adapter.createcompound("AND", p, q)
        assert and_prop.evaluate() is False

        # Test OR
        or_prop = self.adapter.createcompound("OR", p, q)
        assert or_prop.evaluate() is True

        # Test NOT
        not_prop = self.adapter.createcompound("NOT", p)
        assert not_prop.evaluate() is False

        # Test IMPLIES
        implies_prop = self.adapter.createcompound("IMPLIES", p, q)
        assert implies_prop.evaluate() is False

        # Test with lowercase operator name
        or_lower = self.adapter.createcompound("or", p, q)
        assert or_lower.evaluate() is True

        # Test error on unknown operator
        with pytest.raises(ValueError):
            self.adapter.createcompound("UNKNOWN", p, q)

    def test_from_fall_expression(self):
        # Set up propositions in adapter
        p = self.adapter.createproposition("p", True)
        q = self.adapter.createproposition("q", True)
        r = self.adapter.createproposition("r", False)

        # Test simple expression
        expr = self.adapter.fromfallexpression("p AND q")
        assert expr.evaluate() is True

        # Test complex expression
        expr = self.adapter.fromfallexpression("p AND q AND NOT r")
        assert expr.evaluate() is True

        # Test expression with parentheses not supported yet
        with pytest.raises(ValueError):
            self.adapter.fromfallexpression("p AND (q OR r)")


class TestNLPBridge:
    def setup_method(self):
        self.nlp = NLPBridge()

    def test_extract_quantifier(self):
        # Test universal quantifiers
        assert self.nlp.extractquantifier("All men are mortal") == "universal"
        assert self.nlp.extractquantifier("Every student passed the test") == "universal"
        assert self.nlp.extractquantifier("Each person has rights") == "universal"

        # Test existential quantifiers
        assert self.nlp.extractquantifier("Some birds can't fly") == "existential"
        assert self.nlp.extractquantifier("There exists a number that is prime") == "existential"
        assert self.nlp.extractquantifier("There is a cat in the garden") == "existential"

        # Test no quantifier
        assert self.nlp.extractquantifier("Socrates is a man") is None
        assert self.nlp.extractquantifier("The sky is blue") is None

    def test_to_formalities_proposition(self):
        # Test simple statement
        prop = self.nlp.toformalitiesproposition("Socrates is a man", "p")
        assert isinstance(prop, AtomicProposition)
        assert prop.symbol == "p"

        # Test universal quantifier
        prop = self.nlp.toformalitiesproposition("All men are mortal", "q")
        assert isinstance(prop, AtomicProposition)
        assert prop.symbol == "q"

        # Test extractstructure integration
        # This requires more work to validate the structure extraction


class TestSyllogisticReasoning:
    def setup_method(self):
        # Set up adapter and framework
        self.adapter = FormalitiesAdapter()
        self.framework = ClassicalFramework()
        self.validator = Validator(self.framework)
        self.validator.addstrategy(SyntacticValidationStrategy())
        self.validator.addstrategy(LogicalConsistencyStrategy())

    def test_syllogistic_inference_validation(self):
        # Create the premises for "Socrates is a man, All men are mortal, Therefore Socrates is mortal"
        p = self.adapter.createproposition("p", True)  # Socrates is a man
        q = self.adapter.createproposition("q", True)  # All men are mortal
        r = self.adapter.createproposition("r", None)  # Socrates is mortal

        # Create the premises and conclusion
        premises = CompoundProposition(AND(), (p, q))

        # For now, just test if we can validate the proposition structure
        # This doesn't test the semantic validity of the syllogism yet
        inference = CompoundProposition(IMPLIES(), (premises, r))

        # Set up a validation context with structural evaluation mode
        context = ValidationContext(self.framework)
        context.options['evaluation_mode'] = 'structural'  # Use structural mode

        # Test the basic validation (this will pass as we're not checking semantics yet)
        validation_result, _ = self.validator.validate(inference)

        # Just checking the logical structure, not the semantic validity
        assert validation_result.isvalid is True

    def test_invalid_syllogism_structure(self):
        # Set up an invalid structure "Socrates is a man, Trees are plants, Therefore Socrates is mortal"
        p = self.adapter.createproposition("p", True)  # Socrates is a man
        x = self.adapter.createproposition("x", True)  # Trees are plants (unrelated)
        r = self.adapter.createproposition("r", None)  # Socrates is mortal

        # This should still be valid structurally but not semantically
        premises = CompoundProposition(AND(), (p, x))
        inference = CompoundProposition(IMPLIES(), (premises, r))

        # Set up a validation context with structural evaluation mode
        context = ValidationContext(self.framework)
        context.options['evaluation_mode'] = 'structural'  # Use structural mode

        # For now, this will pass as we're only checking logical structure
        validation_result, _ = self.validator.validate(inference)
        assert validation_result.isvalid is True

        # TODO: Create a test for semantic validation once implemented

    def test_semantic_validation_placeholder(self):
        """Placeholder for future semantic validation test."""
        # This test doesn't do anything yet but marks our intention to add semantic validation tests
        pass
