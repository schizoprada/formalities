# ~/formalities/src/formalities/validation/strategies/__init__.py
from .logicalconsistency import LogicalConsistencyStrategy
from .syntactic import SyntacticValidationStrategy

__all__ = ['LogicalConsistencyStrategy', 'SyntacticValidationStrategy']
