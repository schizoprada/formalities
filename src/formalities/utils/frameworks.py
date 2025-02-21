# ~/formalities/src/formalities/utils/frameworks.py
from __future__ import annotations
import typing as t
from dataclasses import dataclass, field
from formalities.core.types.propositions import Proposition
from formalities.core.types.logic import LogicType
from formalities.utils.discovery import frameworkregistry
from formalities.frameworks.base import Framework, ValidationResult
from loguru import logger as log

@dataclass
class FrameworkRequirement:
    """Represents requirements for framework selection"""
    features: list[str] = field(default_factory=list)  # e.g. ["modal", "temporal"]
    operators: list[str] = field(default_factory=list)  # required operators
    logictypes: list[LogicType] = field(default_factory=list)  # required type support

@dataclass
class FrameworkSuggestion:
    """Suggestion result for framework selection"""
    framework: Framework
    compatibility: float  # 0-1 score
    missingfeatures: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


class FrameworkSelector:
    """Handles framework selection and compatibility checking"""

    def __init__(self):
        self._registry = frameworkregistry

    def checkcompatibility(self, proposition: Proposition, framework: Framework) -> ValidationResult:
        """
        Check if a proposition is compatible with a framework

        Args:
            proposition: Proposition to check
            framework: Framework to check against

        Returns:
            ValidationResult with compatibility status and any issues
        """
        try:
            if not framework.iscompatible(proposition):
                return ValidationResult(
                    isvalid=False,
                    errors=[f"Proposition not compatible with {framework.name}"]
                )

            # Validate against framework
            return framework.validate(proposition)

        except Exception as e:
            log.error(f"FrameworkSelector.checkcompatibility | exception | {str(e)}")
            return ValidationResult(
                isvalid=False,
                errors=[f"Compatibility check error: {str(e)}"]
            )

    def validateconstraints(
        self,
        frameworks: list[Framework],
        proposition: Proposition
    ) -> ValidationResult:
        """
        Validate that a set of frameworks can work together for a proposition

        Args:
            frameworks: List of frameworks to check
            proposition: Proposition to validate

        Returns:
            ValidationResult with compatibility status and any issues
        """
        errors = []

        # Check each framework's compatibility
        for fw in frameworks:
            result = self.checkcompatibility(proposition, fw)
            if not result.isvalid:
                errors.extend(result.errors)

        # Check for framework conflicts
        for i, fw1 in enumerate(frameworks):
            for fw2 in frameworks[i+1:]:
                # Basic conflict check - could be enhanced
                if hasattr(fw1, 'conflicts_with') and fw2.__class__.__name__ in fw1.conflicts_with:
                    errors.append(f"Framework conflict: {fw1.name} incompatible with {fw2.name}")

        return ValidationResult(
            (len(errors) == 0),
            errors
        )

    def suggest(
        self,
        requirements: FrameworkRequirement,
        proposition: t.Optional[Proposition] = None
    ) -> list[FrameworkSuggestion]:
        """
        Suggest frameworks matching given requirements

        Args:
            requirements: Required framework features
            proposition: Optional proposition to check compatibility

        Returns:
            List of framework suggestions sorted by compatibility score
        """
        suggestions = []

        # Query available frameworks
        available = self._registry.query(comptype="framework")

        for fwinfo in available:
            try:
                # Load framework class
                fwclass = self._registry.getcomp(fwinfo.name)
                if not fwclass:
                    continue

                framework = fwclass()
                compatibility = 1.0
                missing = []
                notes = []

                # Check features
                fwfeatures = getattr(framework, 'features', [])
                for feat in requirements.features:
                    if feat not in fwfeatures:
                        compatibility *= 0.8
                        missing.append(feat)

                # Check operator support
                fwoperators = getattr(framework, 'supported_operators', [])
                for op in requirements.operators:
                    if op not in fwoperators:
                        compatibility *= 0.9
                        notes.append(f"Missing operator support: {op}")

                # Check type support
                fwtypes = getattr(framework, 'supported_types', [])
                for lt in requirements.logictypes:
                    if lt not in fwtypes:
                        compatibility *= 0.7
                        notes.append(f"Missing type support: {lt}")

                # Check proposition compatibility if provided
                if proposition:
                    compat_result = self.checkcompatibility(proposition, framework)
                    if not compat_result.isvalid:
                        compatibility *= 0.5
                        notes.extend(compat_result.errors)

                suggestions.append(FrameworkSuggestion(
                    framework=framework,
                    compatibility=compatibility,
                    missingfeatures=missing,
                    notes=notes
                ))

            except Exception as e:
                log.error(f"FrameworkSelector.suggest | exception with {fwinfo.name} | {str(e)}")
                continue

        # Sort by compatibility score
        return sorted(
            suggestions,
            key=lambda s: s.compatibility,
            reverse=True
        )

# Global instance
frameworkselector = FrameworkSelector()
