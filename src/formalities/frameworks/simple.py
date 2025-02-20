# ~/formalities/src/formalities/frameworks/simple.py
from __future__ import annotations
import typing as t
from dataclasses import dataclass
from formalities.frameworks.base import Framework, ValidationResult
from formalities.core.types.propositions import (
    Proposition, AtomicProposition, CompoundProposition
)
from formalities.core.types.operators.boolean import (
    AND, OR, NOT, IMPLIES, IFF,
    ANDN, ORN, NAND, NOR
)

class ClassicalFramework(Framework):
    """
    Classical propositional logic framework.
    Implements standard truth-functional semantics where:
        - every proposition is either true or false (law of excluded middle)
        - no proposition can be both true and false (law of non-contradiction) # we should probably define these laws somewhere, potentially with matching custom exceptions
        - truth values are determined by truth tables
    """
    VALIDOPERATORS = (AND, OR, NOT, IMPLIES, IFF, ANDN, ORN, NAND, NOR)
    @property
    def name(self) -> str:
        return "Classical Proposition Logic"

    def _containsconjunction(self, proposition: Proposition, p1: Proposition, p2: Proposition) -> bool:
        """Check if proposition contains a conjunction of p1 and p2"""
        if isinstance(proposition, CompoundProposition):
            if isinstance(proposition.operator, AND):
                comps = set(proposition.components)
                if (p1 in comps) and (p2 in comps):
                    return True
            return any(
                self._containsconjunction(comp, p1, p2)
                for comp in proposition.components
            )
        return False

    def iscompatible(self, proposition: Proposition) -> bool:
        """Check if proposition uses only classical operators."""
        if isinstance(proposition, AtomicProposition):
            return True
        if isinstance(proposition, CompoundProposition):
            if not isinstance(proposition.operator, self.VALIDOPERATORS):
                return False
            return all(
                self.iscompatible(comp)
                for comp in proposition.components
            )
        return False

    def validate(self, proposition: Proposition) -> ValidationResult:
        """
        Validate according to classical logic rules.
        Checks:
            1. All components are valid propositions
            2. No contradictions in compound statements
            3. Operators are truth-functional
        """
        errors = []

        if not self.iscompatible(proposition):
            errors.append(f"Proposition contains operators not supported in classical logic") # this could be more specific about which operators
            return ValidationResult(False, errors)

        # check for contradictions
        if isinstance(proposition, CompoundProposition):
            # check for direct contradictions
            for atom in (atoms:=proposition.atoms):
                notatom = CompoundProposition(NOT(), (atom,))
                if self._containsconjunction(proposition, atom, notatom):
                    errors.append(f"Contradiction found: conjunction of {atom} and {NOT.symbol}{atom}")
        return ValidationResult(
            (len(errors)==0),
            errors
        )

    def evaluate(self, proposition: Proposition, context: t.Optional[dict[str, bool]] = None) -> bool:
        self.validatecompatibility(proposition)
        return proposition.evaluate(context)
