# ~/formalities/src/formalities/validation/strategies/syntactic.py
from __future__ import annotations
import typing as t
from formalities.core.types.propositions import Proposition
from formalities.validation.base import (
    ValidationType, ValidationResult, ValidationContext, ValidationStrategy
)

class SyntacticValidationStrategy(ValidationStrategy):
    @property
    def validationtype(self) -> ValidationType:
        return ValidationType.SYNTACTIC

    def validate(self, proposition: Proposition, context: ValidationContext) -> ValidationResult:
        errors = []
        # add basic syntactic checks
        # for now just ensures proposition can be string-represented
        try:
            str(proposition)
        except Exception as e:
            errors.append(f"Syntactic Error: {str(e)}")

        return ValidationResult(
            (len(errors)==0),
            errors
        )
