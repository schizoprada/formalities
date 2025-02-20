# ~/formalities/src/formalities/core/types/logic.py
from __future__ import annotations
from enum import Enum, auto

class LogicType(Enum):
    """
    Enumeration of fundamental logic types.
    These represent the core building blocks in formal logic.
    """
    PROPOSITION = auto()  # Statements that are true or false
    PREDICATE = auto()    # Properties or relations
    TERM = auto()         # Objects or constants
    SYMBOL = auto()       # Basic elements of formal language
    OPERATOR = auto()     # Logical operations
    QUANTIFIER = auto()   # Quantification expressions
