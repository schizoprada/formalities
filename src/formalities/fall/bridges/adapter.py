# ~/formalities/src/formalities/fall/bridges/adapter.py
from __future__ import annotations
import typing as t
from formalities.core.types.propositions import (
    Proposition, AtomicProposition, CompoundProposition, NumericProposition
)
from formalities.core.types.operators.boolean import (
    AND, OR, NOT, IMPLIES, IFF
)
from formalities.validation.base import ValidationResult
from formalities.core.types.evaluations import EvaluationContext
from loguru import logger as log


class AdaptedCompoundProposition(CompoundProposition):
    """Modified CompoundProposition for Adapter support"""

    def evaluate(self, context: t.Optional[t.Dict[str, bool]] = None, *args, **kwargs) -> bool:
        compvals = [
            comp.evaluate(context) if context is not None
            else comp.evaluate()
            for comp in self.components
        ]
        evaluation = False
        optype = type(self.operator)
        if isinstance(optype, AND):
            return all(compvals)
        elif isinstance(optype, OR):
            return any(compvals)
        elif isinstance(optype, NOT):
            return (not compvals[0])
        elif isinstance(optype, IMPLIES):
            return (not compvals[0]) or (compvals[1])
        elif isinstance(optype, IFF):
            return (compvals[0] == compvals[1])
        else:
            # For other operators, attempt to use their apply method with boolean values
            try:
                # This is a fallback, but may not work for all operators
                return self.operator(*self.components)
            except Exception as e:
                raise ValueError(f"Cannot evaluate with operator {self.operator}: {str(e)}")

class FormalitiesAdapter:
    """
    Adapter between FALL language constructs and formalities core types.
    Handles conversion between FALL propositions and formalities propositions
    """

    def __init__(self):
        self.propositions = {}
        self.operators = {
            "AND": AND(),
            "OR": OR(),
            "NOT": NOT(),
            "IMPLIES": IMPLIES(),
            "IFF": IFF()
        }

    def createproposition(self, name: str, value: t.Optional[bool] = None) -> Proposition:
        prop = AtomicProposition(name, _truthvalue=value) # should probably be able to create other types of propositions, perhaps by using :: to connect e.g. ATOMIC::PROPOSITION
        self.propositions[name] = prop
        return prop

    def getproposition(self, name: str) -> t.Optional[Proposition]:
        return self.propositions.get(name)

    def createcompound(self, operatorname: str, *props) -> Proposition:
        if not (operator:=self.operators.get(operatorname.upper())):
            raise ValueError(f"Unknown Operator: {operatorname}")

        processed = []
        for prop in props:
            # if its already a Proposition, use it directly
            if isinstance(prop, Proposition):
                processed.append(prop)
            elif isinstance(prop, bool):
                # Create a temporary atomic proposition with the boolean value
                temp = AtomicProposition(f"temp-{id(prop)}", _truthvalue=prop)
                processed.append(temp)
            elif isinstance(prop, str):
                processed.append(self.getorcreateproposition(prop))
            else:
                raise TypeError(f"Cannot convert {type(prop)} to Proposition")
        log.info(f"Creating CompoundProposition with Operator: {operatorname}")
        log.info(f"Props: {props}")
        log.info(f"Processed Props: {processed}")
        return AdaptedCompoundProposition(operator, tuple(processed))

    def getorcreateproposition(self, name:str) -> Proposition:
        if (prop:=self.getproposition(name)):
            return prop
        return self.createproposition(name)

    def fromfallexpression(self, expression: str) -> Proposition:
        if ("(" in expression) or (")" in expression):
           raise ValueError(f"Expressions with parentheses are not supported yet: {expression}")
        tokens = expression.strip().split()
        if len(tokens) == 1:
            return self.getorcreateproposition(tokens[0])

        if (tokens[0] == "NOT") and (len(tokens) == 2):
            p = self.getorcreateproposition(tokens[1])
            return self.createcompound("NOT", p)

        if (len(tokens) >= 3) and (tokens[1] in self.operators):
            l = self.getorcreateproposition(tokens[0])
            r = self.fromfallexpression(" ".join(tokens[2:]))
            return self.createcompound(tokens[1], l, r)

        raise ValueError(f"Cannot Parse Expression: {expression}")

    def evaluateproposition(self, prop: Proposition, context: t.Optional[dict[str, bool]] = None) -> bool:
        evalctx = EvaluationContext(context)
        return evalctx.evaluate(prop)
