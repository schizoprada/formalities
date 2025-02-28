# ~/formalities/src/formalities/fall/grammar/keywords.py
from enum import Enum, auto

class TokenType(Enum):
    # Keywords
    DEFINE = auto()
    RULE = auto()
    AXIOM = auto()
    WHERE = auto()
    AS = auto()
    IS = auto()
    AND = auto()
    OR = auto()
    IMPLIES = auto()
    CAN = auto()
    BE = auto()
    PROPOSITION = auto()
    ASSERT = auto()
    BEGIN = auto()
    END = auto()
    PROOF = auto()
    STEP = auto()
    INFER = auto()
    FROM = auto()
    VIA = auto()
    GIVEN = auto()
    PROVE = auto()
    USING = auto()
    QUERY = auto()

    # Symbols
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    ARROW = auto()
    PIPE = auto()
    COMMA = auto()
    COLON = auto()
    DOUBLECOLON = auto()
    ASTERISK = auto()
    COMMENT = auto()
    EOL = auto()  # End of line

    # Literals
    IDENTIFIER = auto()
    STRING = auto()
    NUMBER = auto()

    # Misc
    EOF = auto()
    ERROR = auto()

# Map of keyword strings to token types
KEYWORDS = {
    "DEFINE": TokenType.DEFINE,
    "RULE": TokenType.RULE,
    "AXIOM": TokenType.AXIOM,
    "WHERE": TokenType.WHERE,
    "AS": TokenType.AS,
    "IS": TokenType.IS,
    "AND": TokenType.AND,
    "OR": TokenType.OR,
    "IMPLIES": TokenType.IMPLIES,
    "CAN": TokenType.CAN,
    "BE": TokenType.BE,
    "PROPOSITION": TokenType.PROPOSITION,
    "ASSERT": TokenType.ASSERT,
    "BEGIN": TokenType.BEGIN,
    "END": TokenType.END,
    "PROOF": TokenType.PROOF,
    "STEP": TokenType.STEP,
    "INFER": TokenType.INFER,
    "FROM": TokenType.FROM,
    "VIA": TokenType.VIA,
    "GIVEN": TokenType.GIVEN,
    "PROVE": TokenType.PROVE,
    "USING": TokenType.USING,
    "QUERY": TokenType.QUERY,
}
