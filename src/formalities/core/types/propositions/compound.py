# ~/formalities/src/formalities/core/types/propositions/compound.py
from __future__ import annotations
import typing as t
from dataclasses import dataclass
from formalities.core.types.compound import Compound
from formalities.core.types.logic import LogicType
from formalities.core.types.propositions.base import Proposition
from formalities.core.types.operators.base import Operator


@dataclass(frozen=True)
class CompoundProposition(Proposition, Compound[Proposition]):
    """
    A proposition composed of other propositions combined by a logical operator.

    CompoundProposition allows for building complex logical statements by combining
    atomic or other compound propositions using logical operators.
    """
    _operator: Operator[Proposition]
    _components: tuple[Proposition, ...]

    def __post_init__(self) -> None:
        """Validate the number of components matches operator arity"""
        self._operator.validatearity(*self._components)

    def __str__(self) -> str:
            """String representation using operator symbol and components."""
            if self.operator.arity == 1:
                return f"{self.operator.symbol}{self.components[0]}"
            return f"({(' ' + self.operator.symbol + ' ').join(str(p) for p in self.components)}"

    def __eq__(self, other: t.Any) -> bool:
        """Equality comparison checking operator and components."""
        if not isinstance(other, CompoundProposition):
            return False
        return (
            self.operator.symbol == other.operator.symbol and
            self.components == other.components
        )

    def __hash__(self) -> int:
        """Hash based on operator symbol and components."""
        return hash((self.operator.symbol, self.components))

    @property
    def operator(self) -> Operator[Proposition]:
        return self._operator

    @property
    def components(self) -> tuple[Proposition, ...]:
        return self._components

    @property
    def logictype(self) -> LogicType:
        return LogicType.PROPOSITION

    @property
    def atoms(self) -> set[Proposition]:
        _atoms = set()
        for comp in self.components:
            if isinstance(comp, CompoundProposition):
                _atoms.update(comp.atoms)
            else:
                _atoms.add(comp)
        return _atoms


    def evaluate(self, context: t.Optional[t.Dict[str, bool]]=None, *args, **kwargs) -> bool:
        """Evaluate this compound proposition"""
        return self.operator(
            *[
                comp.evaluate(context) if context is not None else comp.evaluate()
                for comp in self.components
            ]
        )
