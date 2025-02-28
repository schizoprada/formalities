# ~/formalities/src/formalities/validation/base.py
from __future__ import annotations
import typing as t
from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass, field
from formalities.core.types.propositions import Proposition
from formalities.frameworks.base import Framework, ValidationResult
from loguru import logger as log

class ValidationError(Exception):
    """Exception raised for validation errors."""
    pass


class ValidationType(Enum):
    """Types of validation that can be performed."""
    SYNTACTIC = auto()    # Structure and form
    SEMANTIC = auto()     # Meaning and interpretation
    LOGICAL = auto()      # Logical consistency
    FRAMEWORK = auto()    # Framework-specific rules
    CUSTOM = auto()       # User-defined validation

@dataclass
class FrameworkContext:
    """Framework-specific validation context"""
    framework: Framework
    settings: dict[str, t.Any] = field(default_factory=dict)
    metadata: dict[str, t.Any] = field(default_factory=dict)

    def validate(self, proposition: Proposition) -> bool:
        try:
            return self.framework.validate(proposition).isvalid
        except Exception as e:
            log.error(f"FrameworkContext.validate | Exception | {str(e)}")
            return False

@dataclass
class ValidationContext:
    """Context for validation operations."""
    framework: Framework
    options: dict[str, t.Any] = field(default_factory=dict)
    metadata: dict[str, t.Any] = field(default_factory=dict)
    history: list[dict[str, t.Any]] = field(default_factory=list)

    def record(self,
        source: str,
        proposition: Proposition,
        success: bool,
        errors: t.Optional[list[str]] = None
    ) -> None:
        """Record a validation result"""
        self.history.append({
            "source": source,
            "proposition": str(proposition),
            "success": success,
            "errors": errors or [],
            "timestamp": "current_time()"  # TODO: Add proper timestamp
        })

    def createchild(self) -> ValidationContext:
        """Create a new context inheriting from this one"""
        return ValidationContext(
            framework=self.framework,
            options=self.options.copy(),
            metadata=self.metadata.copy(),
            history=self.history.copy()
        )

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

    def validate(self, proposition: Proposition, options: t.Optional[dict[str, t.Any]]=None) -> tuple[ValidationResult, ValidationContext]:
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
        log.debug(f"validator.validate | starting validation with {len(self._strategies)} strategies")
        # Framework validation first
        result = self.framework.validate(proposition)
        log.debug(f"validator.validate | framework validation result: {result}")
        if not result.isvalid:
            context.record(
                source=self.framework.name,
                proposition=proposition,
                success=False,
                errors=result.errors
            )
            return result

        # Strategy validation
        for strategy in self._strategies:
            log.debug(f"validator.validate | running strategy: {strategy.__class__.__name__}")
            sresult = strategy.validate(proposition, context)
            log.debug(f"validator.validate | strategy reslt: {sresult}")
            context.record(
                source=f"strategy:{strategy.__class__.__name__}",
                proposition=proposition,
                success=sresult.isvalid,
                errors=sresult.errors if not sresult.isvalid else None
            )
            if not sresult.isvalid:
                errors.extend(sresult.errors)

        finalresult = ValidationResult(
            (len(errors) == 0),
            errors
        )

        context.record(
            source="validator",
            proposition=proposition,
            success=finalresult.isvalid,
            errors=(finalresult.errors if not finalresult.isvalid else None)
        )

        return finalresult, context
