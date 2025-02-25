# ~/formalities/src/formalities/core/types/operators/modal/registry.py
from __future__ import annotations
import typing as t
from formalities.core.types.registry import Registry
from formalities.core.types.operators.modal.base import ModalOperator

class ModalRegistry(Registry[ModalOperator]):
    """Registry for modal operators.

    Manages the registration and retrieval of modal operators.
    Ensures type safety and uniqueness based on operator symbols.
    """

    @classmethod
    def _validateinstance(cls, instance: ModalOperator) -> None:
        """Validate a modal operator before registration.

        Args:
            instance: The operator to validate

        Raises:
            TypeError: If instance is not a ModalOperator
        """
        if not isinstance(instance, ModalOperator):
            raise TypeError(
                f"Instance must be ModalOperator. Got: {type(instance)}"
            )

    @classmethod
    def _getkey(cls, instance: ModalOperator) -> str:
        """Generate a unique key for the modal operator.

        Uses the operator's symbol as the key since modal operators
        are uniquely identified by their symbols.

        Args:
            instance: The operator to generate key for

        Returns:
            The operator's symbol as its unique key
        """
        return instance.symbol

    @classmethod
    def necessity(cls) -> ModalOperator:
        """Get the necessity (□) operator."""
        from formalities.core.types.operators.modal.base import Necessity
        return cls.register(Necessity())

    @classmethod
    def possibility(cls) -> ModalOperator:
        """Get the possibility (◇) operator."""
        from formalities.core.types.operators.modal.base import Possibility
        return cls.register(Possibility())

    @classmethod
    def always(cls) -> ModalOperator:
        """Get the always (G) operator."""
        from formalities.core.types.operators.modal.base import Always
        return cls.register(Always())

    @classmethod
    def eventually(cls) -> ModalOperator:
        """Get the eventually (F) operator."""
        from formalities.core.types.operators.modal.base import Eventually
        return cls.register(Eventually())

    @classmethod
    def until(cls) -> ModalOperator:
        """Get the until (U) operator."""
        from formalities.core.types.operators.modal.base import Until
        return cls.register(Until())
