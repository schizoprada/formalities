# ~/formalities/src/formalities/core/types/operators/base.py
from __future__ import annotations
import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass
from formalities.core.types.logic import LogicType
from formalities.core.types.atomic import Atomic
from formalities.core.types.propositions.base import Proposition

T = t.TypeVar('T', bound=Proposition)

class Operator(ABC, t.Generic[T]):
    """
    Base class for logical operators.

    Operators act on propositions to form new propositions.
    They are the basic tools for building compound logical statements.
    """

    @property
    def logictype(self) -> LogicType:
        return LogicType.OPERATOR

    @property
    @abstractmethod
    def symbol(self) -> str:
        """The symbolic representation of this operator."""
        pass

    @property
    @abstractmethod
    def arity(self) -> int:
        """Number of operands this operator takes."""
        pass


    def validatearity(self, *operands: T) -> None:
        """Validate that the correct number of operands are provided."""
        if len(operands) != self.arity:
            raise ValueError(
                f"""
                Operator {self.symbol} requires exactly {self.arity} operands.
                Got: {len(operands)}
                """
            )

    @abstractmethod
    def apply(self, *operands: T) -> bool:
        """
        Apply this operator to the given operands.
        Args:
            - *operands: The propositions to operate on
        Returns:
            The result of applying this operator
        Raises:
            ValueError if the wrong number of operands provided
        """
        self.validatearity(*operands)
        pass

    def __call__(self, *args, **kwargs):
        """Short hand for apply method"""
        return self.apply(*args, **kwargs)
