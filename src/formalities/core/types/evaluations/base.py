# ~/formalities/src/formalities/core/types/evaluations/base.py
from __future__ import annotations
import enum, typing as t
from formalities.core.types.propositions import (
    Proposition, AtomicProposition, CompoundProposition, NumericProposition
)
from formalities.core.types.operators import (
    AND, OR, NOT, IMPLIES, IFF
)

class EvaluationMode(enum.Enum):
    STRICT = enum.auto() # Require all propositions to have truth values
    STRUCTURAL = enum.auto() # Evaluate structure only, missing values default to True
    SEMANTIC = enum.auto() # Evaluate semantic validity using additional context
    # consider other potential evaluation modes

class EvaluationContext:
    """Context for evaluating propositions with proper type handling"""

    def __init__(self, values: t.Optional[dict[str, bool]] = None, mode: EvaluationMode = EvaluationMode.STRICT, semctx: t.Optional[dict] = None):
        self.values = (values or {})
        self.mode = mode
        self.cache = {} # cache eval results
        self.semctx = (semctx or {}) # semantic context
        self.missingvals = [] # track propositions with missing values

    def _semanticallyrelated(self, prop: Proposition) -> bool:
        """Check if there are semantic relationships defined for this Proposition"""
        if 'relationships' not in self.semctx:
            return False
        # check for relationships that involve this proposition
        # this is a placeholder for more complex semantic validation
        for rel in self.semctx.get('relationships', []):
            if prop.symbol in rel.get('propositions', []):
                return True
        return False

    def evaluate(self, prop: t.Union[Proposition, bool]) -> bool:
        """Evaluate a proposition or boolean value"""
        if isinstance(prop, bool):
            return prop

        if id(prop) in self.cache:
            return self.cache[id(prop)]
        result = False
        if isinstance(prop, AtomicProposition):
            if prop._truthvalue is not None:
                result = prop._truthvalue
            elif prop.symbol in self.values:
                result = self.values[prop.symbol]
            else:
                if self.mode == EvaluationMode.STRICT:
                    raise ValueError(f"No Truth Value for {prop.symbol}")
                elif self.mode == EvaluationMode.STRUCTURAL:
                    # for strucural default to True
                    result = True
                    self.missingvals.append(prop.symbol)
                elif self.mode == EvaluationMode.SEMANTIC:
                    # use semantic context to determine validity if available
                    if self._semanticallyrelated(prop):
                        result = True
                    else:
                        result = False
                        self.missingvals.append(prop.symbol)
        elif isinstance(prop, CompoundProposition):
            if isinstance(prop.operator, AND):
               result = all(self.evaluate(c) for c in prop.components)
            elif isinstance(prop.operator, OR):
               result = any(self.evaluate(c) for c in prop.components)
            elif isinstance(prop.operator, NOT):
                result = (not self.evaluate(prop.components[0]))
            elif isinstance(prop.operator, IMPLIES):
                pval = self.evaluate(prop.components[0])
                qval = self.evaluate(prop.components[1])
                result = (not pval) or qval
            # add more operators
            else:
                # Generic handling by evaluating components first
                compvals = [self.evaluate(c) for c in prop.components]
                opname = prop.operator.__class__.__name__
                if opname == "ANDN":
                    result = all(compvals)
                elif opname == "ORN":
                    result = any(compvals)
                elif opname == "NAND":
                    result = not all(compvals)
                elif opname == "NOR":
                    result = not any(compvals)
                else:
                    raise ValueError(f"Operator {opname} not directly supported in EvaluationContext")
        else:
            result = bool(prop)

        self.cache[id(prop)] = result
        return result


    @property
    def validationfeedback(self) -> dict:
        """Get feedback about the evaluation for validation purposes"""
        return {
            'mode': self.mode,
            'missingvalues': self.missingvals,
            'validstructure': (len(self.missingvals) == 0) or (self.mode != EvaluationMode.STRICT),
            'semanticvalidation': (self.mode == EvaluationMode.SEMANTIC)
        }
