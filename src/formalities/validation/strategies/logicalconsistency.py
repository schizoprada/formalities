# ~/formalities/src/formalities/validation/strategies/logicalconsistency.py
from __future__ import annotations
import typing as t
from formalities.core.types.propositions import Proposition
from formalities.core.types.evaluations import EvaluationContext
from formalities.validation.base import (
    ValidationType, ValidationResult, ValidationContext, ValidationStrategy
)
from loguru import logger as log

class LogicalConsistencyStrategy(ValidationStrategy):
    @property
    def validationtype(self) -> ValidationType:
        return ValidationType.LOGICAL

    def validate(self, proposition: Proposition, context: ValidationContext) -> ValidationResult:
        errors = []
        try:
            evalctx = EvaluationContext(context.options)
            result = evalctx.evaluate(proposition)
            #result = proposition.evaluate(context.options)
            log.debug(f"logicalconsistencystrategy.validate | evaluation result: {result}")
        except Exception as e:
            log.debug(f"logicalconsistencystrategy.validate | evaluation error: {str(e)}")
            errors.append(f"Evaluation Error: {str(e)}")
        return ValidationResult(
            (len(errors)==0),
            errors
        )
