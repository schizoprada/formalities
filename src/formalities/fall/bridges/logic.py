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
        for premise in premises:
            validation = self.validateproposition(premise)
            if not validation.isvalid:
                return False
        validation = self.validateproposition(conclusion)
        if not validation.isvalid:
            return False
        if self._nlpbridge and self._nlpbridge.enabled:
            result = self._nlpbridge.validateinference(premises, conclusion)
            return result.valid
        return True

    def createproposition(self, name: str, value: t.Optional[bool] = None) -> Proposition:
        """Create an atomic proposition and register it."""
        prop = AtomicProposition(name, _truthvalue=value)
        self._propositions[name] = prop
        return prop

    def createcompound(self, operator_name: str, *props) -> Proposition:
        """Create a compound proposition from an operator name and propositions."""
        if operator_name not in self._operators:
            raise ValueError(f"Unknown operator: {operator_name}")

        operator = self._operators[operator_name]
        return CompoundProposition(operator, props)

    def parseexpression(self, expr: str) -> Proposition:
        """Parse a FALL expression into a Formalities proposition."""
        # Simple parsing for expressions like "p AND q", "NOT p", etc.
        tokens = expr.strip().split()

        # Handle empty expression
        if not tokens:
            raise ValueError("Empty expression")

        # Handle atomic propositions
        if len(tokens) == 1:
            return self._getorcreateprop(tokens[0])

        # Handle IS true/false expressions - Create a new proposition with fixed truth value
        if len(tokens) == 3 and tokens[1].upper() == "IS":
            prop_name = tokens[0]
            truth_value = None

            if tokens[2].upper() in ["TRUE", "T"]:
                truth_value = True
            elif tokens[2].upper() in ["FALSE", "F"]:
                truth_value = False

            # Create a new proposition with specified truth value
            # instead of trying to modify an existing one
            return AtomicProposition(prop_name, _truthvalue=truth_value)

        # Handle NOT (unary operator)
        if tokens[0] == "NOT" and len(tokens) == 2:
            return self.createcompound("NOT", self._getorcreateprop(tokens[1]))

        # Handle binary operators (p AND q, p OR q, etc.)
        if len(tokens) >= 3 and tokens[1] in self._operators:
            left = self._getorcreateprop(tokens[0])
            right = self.parseexpression(" ".join(tokens[2:]))
            return self.createcompound(tokens[1], left, right)

        # Handle complex conditions (p IS true AND q IS true)
        if "AND" in tokens:
            idx = tokens.index("AND")
            left_expr = " ".join(tokens[:idx])
            right_expr = " ".join(tokens[idx+1:])
            left_prop = self.parseexpression(left_expr)
            right_prop = self.parseexpression(right_expr)
            return self.createcompound("AND", left_prop, right_prop)

        # More complex parsing would go here
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
        """Check if a set of propositions is consistent."""
        # For basic consistency, we just check if they can all be true together
        # This is a simplified approach - a more complete would check satisfiability

        # Create conjunction of all propositions
        if len(props) == 1:
            return self.validateproposition(props[0]).isvalid

        compound = CompoundProposition(ANDN(len(props)), props)
        result = self.validateproposition(compound)
        return result.isvalid
