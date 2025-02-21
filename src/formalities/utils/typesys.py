# ~/formalities/src/formalities/utils/typesys.py
from __future__ import annotations
import json, typing as t
from dataclasses import dataclass
from formalities.core.types.logic import LogicType
from formalities.core.types.propositions import (
    Proposition, AtomicProposition, CompoundProposition, NumericProposition
)
from loguru import logger as log


@dataclass
class TypeConversionResult:
    """Result of a type conversion operation"""
    success: bool
    value: t.Optional[t.Any] = None
    error: t.Optional[str] = None

class TypeHandler:
    """Handles type validation and converstion for methodbuilder"""

    @staticmethod
    def _tryjsonparse(v: str) -> tuple[bool, t.Any]:
        try:
            return True, json.loads(v)
        except (json.JSONDecodeError, TypeError):
            return False, v

    @staticmethod
    def _trytypeconversion(v: t.Any, target: type) -> tuple[bool, t.Any]:
        if isinstance(v, str):
            success, parsed = TypeHandler._tryjsonparse(v)
            if success:
                v = parsed
        try:
            if target == list and isinstance(v, (str, tuple, set)):
                if isinstance(v, str):
                    success, parsed = TypeHandler._tryjsonparse(v)
                    return True, list(parsed) if success else [v]
                return True, list(v)
            if target == dict and isinstance(v, str):
                success, parsed = TypeHandler._tryjsonparse(v)
                return True, (parsed if success else None)
            converted = target(v)
            return True, converted
        except (ValueError, TypeError):
            return False, v

    @classmethod
    def validateparams(cls, params: dict[str, t.Any], expected: dict[str, type]) -> list[str]:
        errors = []
        for name, exp in expected.items():
            if name not in params:
                errors.append(f"Missing required parameter: {name}")
                continue
            value = params[name]
            success, converted = cls._trytypeconversion(value, exp)
            if success:
                params[name] = converted
            else:
                errors.append(
                    f"""
                    Invalid type ({type(value).__name__}) for parameter ({name}).
                    Expected: {exp.__name__}
                    """
                )
        return errors

    @staticmethod
    def toprop(value: t.Any, name: str = "value") -> TypeConversionResult:
        """
        Convert a primitive value to appropriate proposition type

        Args:
            value: value to convert
            name: name/symbol for resulting proposition

        Returns:
            TypeConversionResult with converted proposition or error
        """
        try:
            # Numeric types -> NumericProposition
            if isinstance(value, (int, float)):
                return TypeConversionResult(
                    success=True,
                    value=NumericProposition(name, value=value)
                )
            # Boolean -> AtomicProposition
            if isinstance(value, bool):
                return TypeConversionResult(
                    success=True,
                    value=AtomicProposition(name, _truthvalue=value)
                )
            # String -> AtomicProposition
            if isinstance(value, str):
                return TypeConversionResult(
                    success=True,
                    value=AtomicProposition(name)
                )
            # Already a Proposition
            if isinstance(value, Proposition):
                return TypeConversionResult(
                    success=True,
                    value=value
                )

            return TypeConversionResult(
                success=False,
                error=f"Cannot convert type ({type(value).__name__}) to proposition"
            )
        except Exception as e:
            log.error(f"TypeHandler.toprop | exception | {str(e)}")
            return TypeConversionResult(
                success=False,
                error=f"Conversion Error: {str(e)}"
            )


    @staticmethod
    def fromprop(prop: Proposition) -> TypeConversionResult:
        """
        Extract primitive value from proposition if possible

        Args:
            prop: Proposition to convert

        Returns:
            TypeConversionResult with extracted value or error
        """
        try:
            # NumericProposition -> number
            if isinstance(prop, NumericProposition):
                return TypeConversionResult(
                    success=True,
                    value=prop.value
                )

            # AtomicProposition -> bool
            if isinstance(prop, AtomicProposition):
                try:
                    return TypeConversionResult(
                        success=True,
                        value=prop.evaluate()
                    )
                except ValueError:
                    return TypeConversionResult(
                        success=True,
                        value=prop.symbol
                    )

            # CompoundProposition -> bool
            if isinstance(prop, CompoundProposition):
                return TypeConversionResult(
                    success=True,
                    value=prop.evaluate()
                )

            return TypeConversionResult(
                success=False,
                error=f"Cannot convert proposition type {type(prop).__name__} to primitive value"
            )

        except Exception as e:
            log.error(f"TypeHandler.from_proposition | exception | {str(e)}")
            return TypeConversionResult(
                success=False,
                error=f"Conversion error: {str(e)}"
            )


typehandler = TypeHandler()
