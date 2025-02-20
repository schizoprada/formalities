# ~/formalities/src/formalities/validation/base.py
from __future__ import annotations
import typing as t
from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass, field
from formalities.core.types.propositions import Proposition
from formalities.frameworks.base import Framework, ValidationResult

class ValidationType(Enum):
    """Types of validation that can be performed."""
    SYNTACTIC = auto()    # Structure and form
    SEMANTIC = auto()     # Meaning and interpretation
    LOGICAL = auto()      # Logical consistency
    FRAMEWORK = auto()    # Framework-specific rules
    CUSTOM = auto()       # User-defined validation

@dataclass
class ValidationContext:
    """Context for validation operations."""
    framework: Framework
    options: dict[str, t.Any] = field(default_factory=dict)


class ValidationStrategy(ABC):
    """Base class for validation strategies."""

    @property
    @abstractmethod
    def validationtype(self) -> ValidationType:
        """The type of validation this strategy performs."""
        pass

    @abstractmethod
    def validate(
        self,
        proposition: Proposition,
        context: ValidationContext
    ) -> ValidationResult:
        """
        Perform validation according to this strategy.

        Args:
            proposition: The proposition to validate
            context: Validation context including framework and options

        Returns:
            ValidationResult with success status and any errors
        """
        pass


class Validator:
    """Main validator class that orchestrates validation strategies."""
    def __init__(self, framework: Framework):
        self.framework = framework
        self._strategies: list[ValidationStrategy] = []

    def addstrategy(self, strategy: ValidationStrategy) -> None:
        self._strategies.append(strategy)

    def validate(self, proposition: Proposition, options: t.Optional[dict[str, t.Any]]=None) -> ValidationResult:
        """
        Validate a proposition using all registered strategies.

        Args:
            proposition: The proposition to validate
            options: Optional validation options

        Returns:
            Combined ValidationResult from all strategies
        """
        context = ValidationContext(
            framework=self.framework,
            options=(options or {})
        )
        errors = []

        #framework validation first
        result = self.framework.validate(proposition)
        if not result.isvalid:
            errors.extend(result.errors)
            return ValidationResult(False, errors)
        for strategy in self._strategies:
            sresult = strategy.validate(proposition, context)
            if not sresult.isvalid:
                errors.extend(sresult.errors)
        return ValidationResult(
            (len(errors) == 0),
            errors
        )
