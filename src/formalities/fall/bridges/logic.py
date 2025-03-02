# ~/formalities/src/formalities/fall/bridges/logic.py
import typing as t
from loguru import logger as log
from formalities.core.types.propositions import (
    Proposition, AtomicProposition, CompoundProposition, NumericProposition
)
from formalities.core.types.operators.boolean import (
    AND, OR, NOT, IMPLIES, IFF,
    ANDN, ORN, NAND, NOR
)
from formalities.frameworks.base import Framework
from formalities.frameworks.simple import ClassicalFramework
from formalities.validation.base import ValidationResult

class LogicBridge:
    """Bridge between FALL language constructs and Formalities core logic system."""

    def __init__(self, framework: t.Optional[Framework] = None):
        """Initialize the logic bridge with an optional framework."""
        self.framework = framework or ClassicalFramework()
        self._operators = {
            "AND": AND(),
            "OR": OR(),
            "NOT": NOT(),
            "IMPLIES": IMPLIES(),
            "IFF": IFF()
        }
        self._propositions = {}
        self._nlpbridge = None

    @property
    def nlpbridge(self):
        return self._nlpbridge

    @nlpbridge.setter
    def nlpbridge(self, bridge):
        self._nlpbridge = bridge

    def validateinference(self, premises: t.List[Proposition], conclusion: Proposition) -> bool:
        """
        Validate inference by checking premises and conclusion, logging inputs and results.
        """
        log.debug(f"Validating inference | Premises: {premises} | Conclusion: {conclusion}")

        for premise in premises:
            validation = self.validateproposition(premise)
            log.info(f"Validated premise: {premise} | Result: {validation.isvalid}")
            if not validation.isvalid:
                log.warning(f"Invalid premise found: {premise}")
                return False

        validation = self.validateproposition(conclusion)
        log.info(f"Validated conclusion: {conclusion} | Result: {validation.isvalid}")
        if not validation.isvalid:
            log.warning(f"Invalid conclusion: {conclusion}")
            return False

        if self._nlpbridge and self._nlpbridge.enabled:
            result = self._nlpbridge.validateinference(premises, conclusion)
            log.info(f"NLPBridge inference validation result: {result.valid}")
            return result.valid

        log.debug("Inference validation successful (default logic path).")
        return True

    def createproposition(self, name: str, value: t.Optional[bool] = None) -> Proposition:
        """Create an atomic proposition and register it."""
        prop = AtomicProposition(name, _truthvalue=value)
        self._propositions[name] = prop
        return prop

    def createcompound(self, operatorname: str, *props) -> Proposition:
        """Create a compound proposition from an operator name and propositions."""
        if operatorname not in self._operators:
            raise ValueError(f"Unknown operator: {operatorname}")

        operator = self._operators[operatorname]
        return CompoundProposition(operator, props)

    def parseexpression(self, expr: str) -> Proposition:
        """
        Parse a FALL expression into a Formalities proposition, logging input and parsed result.
        """
        log.debug(f"Parsing expression: {expr}")
        tokens = expr.strip().split()

        if not tokens:
            log.error("Empty expression encountered.")
            raise ValueError("Empty expression")

        if len(tokens) == 1:
            prop = self._getorcreateprop(tokens[0])
            log.info(f"Parsed atomic proposition: {prop}")
            return prop

        if len(tokens) == 3 and tokens[1].upper() == "IS":
            propname = tokens[0]
            truthvalue = None

            if tokens[2].upper() in ["TRUE", "T"]:
                truthvalue = True
            elif tokens[2].upper() in ["FALSE", "F"]:
                truthvalue = False

            prop = AtomicProposition(propname, _truthvalue=truthvalue)
            log.info(f"Parsed IS expression: {expr} -> {prop}")
            return prop

        if tokens[0] == "NOT" and len(tokens) == 2:
            prop = self.createcompound("NOT", self._getorcreateprop(tokens[1]))
            log.info(f"Parsed NOT expression: {expr} -> {prop}")
            return prop

        if len(tokens) >= 3 and tokens[1] in self._operators:
            left = self._getorcreateprop(tokens[0])
            right = self.parseexpression(" ".join(tokens[2:]))
            prop = self.createcompound(tokens[1], left, right)
            log.info(f"Parsed binary expression: {expr} -> {prop}")
            return prop

        if "AND" in tokens:
            idx = tokens.index("AND")
            lexpr = " ".join(tokens[:idx])
            rexpr = " ".join(tokens[idx+1:])
            lprop = self.parseexpression(lexpr)
            rprop = self.parseexpression(rexpr)
            prop = self.createcompound("AND", lprop, rprop)
            log.info(f"Parsed AND expression: {expr} -> {prop}")
            return prop

        log.error(f"Failed to parse expression: {expr}")
        raise ValueError(f"Cannot parse expression: {expr}")


    def _getorcreateprop(self, name: str) -> Proposition:
        """Get a proposition by name or create if it doesn't exist."""
        if name in self._propositions:
            return self._propositions[name]
        return self.createproposition(name)

    def validateproposition(self, prop: Proposition) -> ValidationResult:
        """Validate a proposition using the current framework."""
        return self.framework.validate(prop)

    def evaluate(self, prop: Proposition, context: t.Optional[dict] = None) -> bool:
        """Evaluate a proposition with the current framework."""
        return self.framework.evaluate(prop, context)

    def registerprop(self, name: str, prop: Proposition) -> None:
        """Register an existing proposition with a name."""
        self._propositions[name] = prop

    def getprop(self, name: str) -> t.Optional[Proposition]:
        """Get a proposition by name."""
        return self._propositions.get(name)

    def isconsistent(self, *props: Proposition) -> bool:
        """
        Check if a set of propositions is consistent, logging the results.
        """
        log.debug(f"Checking consistency for propositions: {props}")

        if len(props) == 1:
            result = self.validateproposition(props[0]).isvalid
            log.info(f"Single proposition consistency check: {props[0]} | Result: {result}")
            return result

        compound = CompoundProposition(ANDN(len(props)), props)
        result = self.validateproposition(compound)

        log.info(f"Compound proposition consistency check: {compound} | Result: {result.isvalid}")
        return result.isvalid
