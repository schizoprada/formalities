# ~/formalities/src/formalities/fall/runtime/validator.py
import typing as t
from dataclasses import dataclass, field
from loguru import logger as log
from formalities.fall.bridges.logic import LogicBridge
from formalities.fall.parser.abstract import (
    PropositionDefinition, Assertion, RuleDefinition,
    AxiomDefinition, Proof, ProofStep
)
from formalities.core.types.propositions import Proposition
from formalities.validation.base import ValidationResult

class ValidationError(Exception):
    """Exception raised when validation fails."""
    pass

@dataclass
class ValidationContext:
    """Context for validation operations within FALL."""
    bridge: LogicBridge
    rules: dict[str, RuleDefinition] = field(default_factory=dict)
    axioms: dict[str, AxiomDefinition] = field(default_factory=dict)
    options: dict[str, t.Any] = field(default_factory=dict)
    metadata: dict[str, t.Any] = field(default_factory=dict)
    history: list[dict[str, t.Any]] = field(default_factory=list)

    def record(self, source: str, success: bool, errors: t.Optional[list[str]] = None) -> None:
        """Record a validation result"""
        self.history.append({
            "source": source,
            "success": success,
            "errors": errors or [],
            "timestamp": "current_time()"  # TODO: Add proper timestamp
        })

class FallValidator:
    """Validator for FALL language constructs."""

    def __init__(self, bridge: t.Optional[LogicBridge] = None):
        """Initialize the validator with an optional logic bridge."""
        self.bridge = bridge or LogicBridge()
        self.context = ValidationContext(self.bridge)

    def validateproposition(self, propdef: PropositionDefinition) -> ValidationResult:
        """
        Validate a proposition definition, logging detailed validation decisions and reasons.
        """
        log.debug(f"Validating proposition: {propdef.name}")
        errors = []

        if not propdef.name or not propdef.name.isalnum():
            errors.append(f"Invalid proposition name: {propdef.name}")
        if not propdef.text:
            errors.append("Proposition text cannot be empty")
        for key, value in propdef.structure.items():
            if not key or not value:
                errors.append(f"Invalid structure element: {key} = {value}")

        try:
            logprop = self.bridge.createproposition(propdef.name)
            propvalidation = self.bridge.validateproposition(logprop)
            if not propvalidation.isvalid:
                errors.extend(propvalidation.errors)
        except Exception as e:
            log.error(f"Logic validation error for proposition '{propdef.name}': {str(e)}")
            errors.append(f"Logic error: {str(e)}")

        result = ValidationResult(len(errors) == 0, errors)
        log.info(f"Proposition validation result: {propdef.name} | Valid: {result.isvalid} | Errors: {errors}")
        self.context.record(
            source=f"proposition:{propdef.name}",
            success=result.isvalid,
            errors=errors if not result.isvalid else None
        )
        return result


    def validateassertion(self, assertion: Assertion) -> ValidationResult:
        """Validate a logical assertion."""
        errors = []

        if not assertion.expression:
            errors.append("Assertion expression cannot be empty")
            return ValidationResult(False, errors)

        # Parse the expression into a logical proposition
        try:
            logprop = self.bridge.parseexpression(assertion.expression)
            propvalidation = self.bridge.validateproposition(logprop)
            if not propvalidation.isvalid:
                errors.extend(propvalidation.errors)
        except Exception as e:
            #log.error(f"Expression validation error: {str(e)}")
            errors.append(f"Expression error: {str(e)}")

        result = ValidationResult(len(errors) == 0, errors)
        self.context.record(
            source=f"assertion:{assertion.expression}",
            success=result.isvalid,
            errors=errors if not result.isvalid else None
        )
        return result

    def validateproof(self, proof: Proof) -> ValidationResult:
        """Validate a proof."""
        errors = []

        # Check that all given propositions exist
        for propname in proof.given:
            if not self.bridge.getprop(propname):
                errors.append(f"Unknown given proposition: {propname}")

        # Check that the proposition to prove exists
        if not self.bridge.getprop(proof.prove):
            errors.append(f"Unknown proposition to prove: {proof.prove}")

        # Check that all axioms used exist
        for axiomname in proof.using:
            if axiomname not in self.context.axioms:
                errors.append(f"Unknown axiom: {axiomname}")

        # Check each proof step
        stepprops = {}  # Track propositions established in each step
        for step in proof.steps:
            # Simple validation for now, more complex validation in executor
            if step.action.startswith("ASSERT"):
                try:
                    expr = step.action.replace("ASSERT", "", 1).strip()
                    logprop = self.bridge.parseexpression(expr)
                    stepprops[f"step{step.number}"] = logprop
                except Exception as e:
                    errors.append(f"Step {step.number} error: {str(e)}")
            elif step.action.startswith("INFER"):
                # For inference steps, check sources and axiom
                if not step.source:
                    errors.append(f"Step {step.number} has no source")
                if not step.via:
                    errors.append(f"Step {step.number} has no axiom")
                if step.via and step.via not in self.context.axioms:
                    errors.append(f"Step {step.number} uses unknown axiom: {step.via}")

        result = ValidationResult(len(errors) == 0, errors)
        self.context.record(
            source=f"proof:{proof.prove}",
            success=result.isvalid,
            errors=errors if not result.isvalid else None
        )
        return result

    def validateaxiom(self, axiom: AxiomDefinition) -> ValidationResult:
        """Validate an axiom definition."""
        errors = []

        # Check that the axiom name is valid
        if not axiom.name or not axiom.name.isalnum():
            errors.append(f"Invalid axiom name: {axiom.name}")

        # Check that there is at least one condition
        if not axiom.conditions:
            errors.append("Axiom must have at least one condition")

        # Validate each condition expression
        for condition in axiom.conditions:
            try:
                logprop = self.bridge.parseexpression(condition.expression)
                propvalidation = self.bridge.validateproposition(logprop)
                if not propvalidation.isvalid:
                    errors.extend(propvalidation.errors)
            except Exception as e:
                errors.append(f"Condition error: {str(e)}")

        result = ValidationResult(len(errors) == 0, errors)
        self.context.record(
            source=f"axiom:{axiom.name}",
            success=result.isvalid,
            errors=errors if not result.isvalid else None
        )
        return result

    def validaterule(self, rule: RuleDefinition) -> ValidationResult:
        """Validate a rule definition."""
        errors = []

        # Check that the rule name is valid
        if not rule.name or not rule.name.isalnum():
            errors.append(f"Invalid rule name: {rule.name}")

        # Check that there is at least one condition
        if not rule.conditions:
            errors.append("Rule must have at least one condition")

        result = ValidationResult(len(errors) == 0, errors)
        self.context.record(
            source=f"rule:{rule.name}",
            success=result.isvalid,
            errors=errors if not result.isvalid else None
        )
        return result
