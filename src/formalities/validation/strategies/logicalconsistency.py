# ~/formalities/src/formalities/validation/strategies/logicalconsistency.py
from __future__ import annotations
import typing as t
from formalities.core.types.propositions import Proposition
from formalities.validation.base import (
    ValidationType, ValidationResult, ValidationContext, ValidationStrategy
)

class LogicalConsistencyStrategy(ValidationStrategy):
    @property
    def validationtype(self) -> ValidationType:
        return ValidationType.LOGICAL

    def validate(self, proposition: Proposition, context: ValidationContext) -> ValidationResult:
        errors = []
        try:
            proposition.evaluate() # why is context not being used here?
        except Exception as e:
            errors.append(f"Evaluation Error: {str(e)}")
        return ValidationResult(
            (len(errors)==0),
            errors
        )
