# ~/formalities/tests/fall/test_lexer.py
import pytest
from formalities.fall.parser.lexing import Lexer
from formalities.fall.grammar.keywords import TokenType

def test_basic_lexing():
    source = """
    !- Test FALL program
    DEFINE RULE TestRule
    WHERE WORD "test" IS NOUN //

    DEFINE PROPOSITION p AS "This is a test"
    WHERE "test" IS NOUN //

    ASSERT p -> q //
    """

    lexer = Lexer(source)
    tokens = lexer.scantokens()

    # Check if keywords are properly recognized
    assert any(t.type == TokenType.DEFINE for t in tokens)
    assert any(t.type == TokenType.RULE for t in tokens)
    assert any(t.type == TokenType.WHERE for t in tokens)
    assert any(t.type == TokenType.PROPOSITION for t in tokens)
    assert any(t.type == TokenType.ASSERT for t in tokens)

    # Check if identifiers are recognized
    assert any(t.type == TokenType.IDENTIFIER and t.lexeme == "TestRule" for t in tokens)
    assert any(t.type == TokenType.IDENTIFIER and t.lexeme == "p" for t in tokens)
    assert any(t.type == TokenType.IDENTIFIER and t.lexeme == "q" for t in tokens)

    # Check if string literals are recognized
    assert any(t.type == TokenType.STRING and t.value == "test" for t in tokens)
    assert any(t.type == TokenType.STRING and t.value == "This is a test" for t in tokens)

    # Check if comments are recognized
    assert any(t.type == TokenType.COMMENT for t in tokens)

    # Check if end of lines are recognized
    assert any(t.type == TokenType.EOL for t in tokens)
