# ~/formalities/src/formalities/fall/parser/lexing.py
import typing as t
from dataclasses import dataclass
from formalities.fall.grammar.keywords import TokenType, KEYWORDS

@dataclass
class Token:
    type: TokenType
    lexeme: str
    line: int
    column: int
    value: t.Optional[object] = None

class Lexer:
    def __init__(self, source: str):
        self.source = source
        self.tokens: t.List[Token] = []
        self.start = 0
        self.current = 0
        self.line = 1
        self.column = 1

        # Define token patterns for single-character tokens
        self.char_tokens = {
            '(': TokenType.LPAREN,
            ')': TokenType.RPAREN,
            '[': TokenType.LBRACKET,
            ']': TokenType.RBRACKET,
            ',': TokenType.COMMA,
            '*': TokenType.ASTERISK,
            '|': TokenType.PIPE,
        }

        # Define token patterns for two-character tokens
        self.double_char_tokens = {
            '->': TokenType.ARROW,
            '::': TokenType.DOUBLECOLON,
            '//': TokenType.EOL,
            '!-': TokenType.COMMENT,
        }

    def scantokens(self) -> t.List[Token]:
        """Scan the source code and return a list of tokens."""
        while not self._reachedend():
            # Beginning of the next lexeme
            self.start = self.current
            self._scantoken()

        self.tokens.append(Token(TokenType.EOF, "", self.line, self.column))
        return self.tokens

    def _scantoken(self) -> None:
        """Scan a single token."""
        c = self._advance()

        # Check for single character tokens first
        if c in self.char_tokens:
            self._addtoken(self.char_tokens[c])
            return

        # Check for potential double character tokens
        if self.current < len(self.source):
            double_char = c + self._peek()
            if double_char in self.double_char_tokens:
                self._advance()  # Consume the second character
                token_type = self.double_char_tokens[double_char]

                # Special handling for comments
                if token_type == TokenType.COMMENT:
                    # Comment goes until the end of the line or file
                    while self._peek() != '\n' and not self._reachedend():
                        self._advance()

                self._addtoken(token_type)
                return

        # Handle whitespace
        if c in [' ', '\t', '\r']:
            # Ignore whitespace
            return
        elif c == '\n':
            self.line += 1
            self.column = 0
            self._addtoken(TokenType.EOL)
            return

        # Handle other single character tokens that need special logic
        if c == ':':
            self._addtoken(TokenType.COLON)
            return

        # Handle string literals
        if c == '"':
            self._string()
            return

        # Handle identifiers and keywords
        if self._isalpha(c):
            self._identifier()
            return

        # Handle numbers
        if self._isdigit(c):
            self._number()
            return

        # If we get here, the character wasn't recognized
        self._addtoken(TokenType.ERROR, f"Unexpected character: '{c}'")

    def _string(self) -> None:
        """Process a string literal."""
        while self._peek() != '"' and not self._reachedend():
            if self._peek() == '\n':
                self.line += 1
                self.column = 0
            self._advance()

        if self._reachedend():
            self._addtoken(TokenType.ERROR, "Unterminated string")
            return

        # The closing "
        self._advance()

        # Trim the surrounding quotes
        value = self.source[self.start + 1:self.current - 1]
        self._addtoken(TokenType.STRING, value)

    def _identifier(self) -> None:
        """Process an identifier or keyword."""
        while not self._reachedend() and self._isalphanumeric(self._peek()):
            self._advance()

        text = self.source[self.start:self.current]
        type = KEYWORDS.get(text.upper(), TokenType.IDENTIFIER)
        self._addtoken(type)

    def _number(self) -> None:
        """Process a number literal."""
        while not self._reachedend() and self._isdigit(self._peek()):
            self._advance()

        # Look for a decimal part
        if not self._reachedend() and self._peek() == '.' and not self._reachedend(self.current + 1) and self._isdigit(self._peeknext()):
            # Consume the "."
            self._advance()

            while not self._reachedend() and self._isdigit(self._peek()):
                self._advance()

        value = float(self.source[self.start:self.current])
        self._addtoken(TokenType.NUMBER, value)

    def _reachedend(self, pos: t.Optional[int] = None) -> bool:
        """Check if we've reached the end of the source at the given position (or current position if None)."""
        if pos is None:
            pos = self.current
        return (pos >= len(self.source))

    def _isalpha(self, c: str) -> bool:
        return (c.isalpha() or c == '_')

    def _isalphanumeric(self, c: str) -> bool:
        return (c.isalnum() or c == '_')

    def _isdigit(self, c: str) -> bool:
        return c.isdigit()

    def _addtoken(self, type: TokenType, literal: t.Optional[object] = None) -> None:
        text = self.source[self.start:self.current]
        self.tokens.append(Token(type, text, self.line, (self.column - (self.current - self.start)), literal))

    def _peek(self) -> str:
        if self._reachedend():
            return '\0'
        return self.source[self.current]

    def _peeknext(self) -> str:
        if self._reachedend(self.current + 1):
            return '\0'
        return self.source[self.current + 1]

    def _advance(self) -> str:
        c = self.source[self.current]
        self.current += 1
        self.column += 1
        return c

    def _match(self, expected: str) -> bool:
        if self._reachedend():
            return False
        if self.source[self.current] != expected:
            return False
        self.current += 1
        self.column += 1
        return True
