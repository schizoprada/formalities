# ~/formalities/src/formalities/fall/parser/parsing.py
# ~/formalities/src/formalities/fall/parser/parsing.py
import re, typing as t
from formalities.fall.parser.lexing import Token, Lexer
from formalities.fall.parser.abstract import (
    Node, Program, RuleDefinition, AxiomDefinition,
    PropositionDefinition, Assertion, Proof, ProofStep, Query, Condition
)
from formalities.fall.grammar.keywords import TokenType
from loguru import logger as log


class ParseError(Exception):
    """Exception raised for errors during parsing."""
    pass

class Parser:
    def __init__(self, tokens: t.List[Token]):
        self.tokens = tokens
        self.current = 0

    def parse(self) -> Program:
        """Parse the tokens into an AST."""
        statements = []

        while not self._reachedend():
            try:
                # Check for BEGIN PROOF sequence
                if self._check(TokenType.BEGIN) and self._checknext(TokenType.PROOF):
                    # Handle proof as a special case
                    proof_statement = self._parseproof()
                    if proof_statement:
                        statements.append(proof_statement)
                        #log.info(f"Added Proof Statement to Program")
                else:
                    # Regular statement parsing
                    stmt = self._declaration()
                    if stmt:
                        statements.append(stmt)
                        #log.info(f"Added Statement to Program: {type(stmt).__name__}")
            except ParseError as e:
                # Skip to the next statement for error recovery
                #log.error(f"Parser Error: {str(e)}")
                self._synchronize()

        result = Program(statements)
        #log.info(f"Created Program with {len(statements)} Statements")
        return result

    def _parseproof(self) -> Proof:
        """Parse a full proof structure from BEGIN PROOF to END PROOF."""
        # Consume BEGIN PROOF
        self._consume(TokenType.BEGIN, "Expected BEGIN")
        self._consume(TokenType.PROOF, "Expected PROOF after BEGIN")

        # Skip any EOL tokens
        while self._check(TokenType.EOL):
            self._advance()

        # Parse GIVEN statements
        given = []
        while self._check(TokenType.GIVEN):
            self._advance()  # Consume GIVEN
            given.append(self._consume(TokenType.IDENTIFIER, "Expected proposition identifier after GIVEN").lexeme)
            # Skip any EOL tokens
            while self._check(TokenType.EOL):
                self._advance()

        # Parse PROVE statement
        self._consume(TokenType.PROVE, "Expected PROVE in proof")
        prove = self._consume(TokenType.IDENTIFIER, "Expected proposition identifier").lexeme
        # Skip any EOL tokens
        while self._check(TokenType.EOL):
            self._advance()

        # Parse USING statement
        self._consume(TokenType.USING, "Expected USING after PROVE")
        using = []
        using.append(self._consume(TokenType.IDENTIFIER, "Expected identifier after USING").lexeme)
        while self._match(TokenType.COMMA):
            using.append(self._consume(TokenType.IDENTIFIER, "Expected identifier after comma").lexeme)
        # Skip any EOL tokens
        while self._check(TokenType.EOL):
            self._advance()

        # Parse proof steps
        steps = []
        while self._check(TokenType.STEP):
            # Parse step number
            self._advance()  # Consume STEP
            step_num = int(float(self._consume(TokenType.NUMBER, "Expected step number").value))
            self._consume(TokenType.COLON, "Expected colon after step number")

            # Parse step action (ASSERT or INFER)
            action = None
            expr = None
            source = None
            via = None

            if self._match(TokenType.ASSERT):
                action = "ASSERT"
                # Collect tokens until EOL for the expression
                exprtokens = []
                while not self._check(TokenType.EOL) and not self._check(TokenType.EOF):
                    exprtokens.append(self._advance().lexeme)
                expr = " ".join(exprtokens)
            elif self._match(TokenType.INFER):
                action = "INFER"
                # Get proposition being inferred
                expr = self._consume(TokenType.IDENTIFIER, "Expected proposition identifier").lexeme

                # Parse FROM clause
                source = []
                if self._match(TokenType.FROM):
                    self._consume(TokenType.LBRACKET, "Expected [ after FROM")
                    source.append(self._consume(TokenType.IDENTIFIER, "Expected identifier").lexeme)
                    while self._match(TokenType.COMMA):
                        source.append(self._consume(TokenType.IDENTIFIER, "Expected identifier after comma").lexeme)
                    self._consume(TokenType.RBRACKET, "Expected ] after sources")

                # Parse VIA clause
                if self._match(TokenType.VIA):
                    via = self._consume(TokenType.IDENTIFIER, "Expected axiom name after VIA").lexeme
            else:
                raise ParseError(f"Expected ASSERT or INFER in step, got {self._peek().type}")

            # Add the step to our list
            steps.append(ProofStep(step_num, f"{action} {expr}", source, via))

            # Skip any EOL tokens
            while self._check(TokenType.EOL):
                self._advance()

        # Parse END PROOF
        self._consume(TokenType.END, "Expected END")
        self._consume(TokenType.PROOF, "Expected PROOF after END")

        # Skip any EOL tokens
        while self._check(TokenType.EOL):
            self._advance()

        return Proof(given, prove, using, steps)

    def _declaration(self) -> t.Optional[Node]:
        """Parse a declaration statement."""
        # Skip EOL and comments
        while self._check(TokenType.EOL) or self._check(TokenType.COMMENT):
            self._advance()

        if self._reachedend():
            return None

        if self._match(TokenType.DEFINE):
            return self._definition()
        elif self._match(TokenType.ASSERT):
            return self._assertion()
        elif self._match(TokenType.BEGIN):
            # Check for BEGIN PROOF sequence
            if self._check(TokenType.PROOF):
                return self._proof()
            else:
                raise ParseError(f"Expected PROOF after BEGIN, got {self._peek().type}")
        elif self._match(TokenType.QUERY):
            return self._query()

        raise ParseError(f"Expected declaration, got {self._peek().type}")

    def _definition(self) -> Node:
        """Parse a definition statement."""
        if self._match(TokenType.RULE):
            return self._ruledef()
        elif self._match(TokenType.AXIOM):
            return self._axiomdef()
        elif self._match(TokenType.PROPOSITION):
            return self._propositiondef()

        raise ParseError(f"Expected RULE, AXIOM, or PROPOSITION, got {self._peek().type}")

    def _ruledef(self) -> RuleDefinition:
        """Parse a rule definition."""
        name = self._consume(TokenType.IDENTIFIER, "Expected rule name").lexeme
        conditions = self._conditions()
        return RuleDefinition(name, conditions)

    def _axiomdef(self) -> AxiomDefinition:
        """Parse an axiom definition."""
        name = self._consume(TokenType.IDENTIFIER, "Expected axiom name").lexeme
        self._consume(TokenType.WHERE, "Expected WHERE after axiom name")

        # Parse condition expression
        expr = self._parsexpr()
        # Normalize case of TRUE/FALSE to ensure consistent parsing
        expr = re.sub(r'\bTRUE\b', 'true', expr, flags=re.IGNORECASE)
        expr = re.sub(r'\bFALSE\b', 'false', expr, flags=re.IGNORECASE)

        conditions = [Condition(expr)]

        self._consume(TokenType.EOL, "Expected end of line after conditions")
        return AxiomDefinition(name, conditions)

    def _propositiondef(self) -> PropositionDefinition:
        """Parse a proposition definition."""
        name = self._consume(TokenType.IDENTIFIER, "Expected proposition name").lexeme
        #log.debug(f"Parsing Proposition: {name}")
        self._consume(TokenType.AS, "Expected AS after proposition name")
        text = self._consume(TokenType.STRING, "Expected string for proposition text").value
        structure = self._structure()
        return PropositionDefinition(name, text, structure)

    def _conditions(self) -> t.List[Condition]:
        """Parse a list of conditions."""
        conditions = []
        self._consume(TokenType.WHERE, "Expected WHERE after name")

        # Parse condition
        expr = self._parsexpr()
        conditions.append(Condition(expr))

        # Parse additional conditions with AND
        while self._match(TokenType.AND):
            expr = self._parsexpr()
            conditions.append(Condition(expr))

        self._consume(TokenType.EOL, "Expected end of line after conditions")
        return conditions

    def _structure(self) -> t.Dict[str, t.Any]:
        """Parse a structure definition."""
        structure = {}
        self._consume(TokenType.WHERE, "Expected WHERE after text")

        # Parse simple key-value pairs for now
        key = self._consume(TokenType.STRING, "Expected string key").value
        self._consume(TokenType.IS, "Expected IS after key")
        value = self._parsexpr()
        structure[key] = value

        # Additional structure elements with AND
        while self._match(TokenType.AND):
            key = self._consume(TokenType.STRING, "Expected string key").value
            self._consume(TokenType.IS, "Expected IS after key")
            value = self._parsexpr()
            structure[key] = value

        self._consume(TokenType.EOL, "Expected end of line after structure")
        return structure

    def _assertion(self) -> Assertion:
        """Parse an assertion statement."""
        expr = self._parsexpr()
        self._consume(TokenType.EOL, "Expected end of line after assertion")
        return Assertion(expr)

    def _proof(self) -> Proof:
        """Parse a proof block."""
        self._consume(TokenType.PROOF, "Expected PROOF after BEGIN")

        # Skip any EOL tokens
        while self._check(TokenType.EOL):
            self._advance()

        # Parse GIVEN
        given = []
        while self._check(TokenType.GIVEN):
            self._advance()  # Consume GIVEN
            given.append(self._consume(TokenType.IDENTIFIER, "Expected proposition identifier after GIVEN").lexeme)

            # Optionally consume EOL
            while self._check(TokenType.EOL):
                self._advance()

        # Parse PROVE
        self._consume(TokenType.PROVE, "Expected PROVE in proof")
        prove = self._consume(TokenType.IDENTIFIER, "Expected proposition identifier").lexeme

        # Optionally consume EOL
        while self._check(TokenType.EOL):
            self._advance()

        # Parse USING
        self._consume(TokenType.USING, "Expected USING after PROVE")
        using = []
        using.append(self._consume(TokenType.IDENTIFIER, "Expected identifier after USING").lexeme)
        while self._match(TokenType.COMMA):
            using.append(self._consume(TokenType.IDENTIFIER, "Expected identifier after comma").lexeme)

        # Optionally consume EOL
        while self._check(TokenType.EOL):
            self._advance()

        # Parse STEPS
        steps = []
        while self._check(TokenType.STEP):
            step = self._proofstep()
            steps.append(step)

            # Optionally consume EOL
            while self._check(TokenType.EOL):
                self._advance()

        # Final END PROOF
        self._consume(TokenType.END, "Expected END")
        self._consume(TokenType.PROOF, "Expected PROOF after END")

        # Consume any remaining EOL
        while self._check(TokenType.EOL):
            self._advance()

        return Proof(given, prove, using, steps)

    def _proofstep(self) -> ProofStep:
        """Parse a proof step."""
        self._consume(TokenType.STEP, "Expected STEP in proof")

        number = int(float(self._consume(TokenType.NUMBER, "Expected step number").value))
        self._consume(TokenType.COLON, "Expected colon after step number")

        source = None
        via = None

        if self._match(TokenType.ASSERT):
            action = "ASSERT"
            expr = self._parsexpr()
        elif self._match(TokenType.INFER):
            action = "INFER"
            expr = self._consume(TokenType.IDENTIFIER, "Expected proposition identifier after INFER").lexeme

            # Parse FROM
            source = []
            if self._match(TokenType.FROM):
                self._consume(TokenType.LBRACKET, "Expected [ after FROM")
                source.append(self._consume(TokenType.IDENTIFIER, "Expected identifier").lexeme)
                while self._match(TokenType.COMMA):
                    source.append(self._consume(TokenType.IDENTIFIER, "Expected identifier after comma").lexeme)
                self._consume(TokenType.RBRACKET, "Expected ] after sources")

            # Parse VIA
            if self._match(TokenType.VIA):
                via = self._consume(TokenType.IDENTIFIER, "Expected axiom name after VIA").lexeme
        else:
            raise ParseError(f"Expected ASSERT or INFER in step, got {self._peek().type}")

        self._consume(TokenType.EOL, "Expected end of line after step")
        return ProofStep(number, f"{action} {expr}", source, via)

    def _query(self) -> Query:
        """Parse a query statement."""
        prop = self._consume(TokenType.IDENTIFIER, "Expected proposition identifier").lexeme
        self._consume(TokenType.EOL, "Expected end of line after query")
        return Query(prop)

    def _parsexpr(self) -> str:
        """Parse an expression (simplified for now, returning raw text)."""
        # For a quick implementation, we'll just capture the tokens until EOL
        # and join them to create the expression string
        exprtokens = []
        while not self._check(TokenType.EOL) and not self._reachedend():
            exprtokens.append(self._advance().lexeme)
        return " ".join(exprtokens)

    # Helper methods
    def _reachedend(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _peeknext(self) -> Token:
        if self.current + 1 >= len(self.tokens):
            return self.tokens[self.current]  # Return EOF token
        return self.tokens[self.current + 1]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _advance(self) -> Token:
        if not self._reachedend():
            self.current += 1
        return self._previous()

    def _check(self, type: TokenType) -> bool:
        if self._reachedend():
            return False
        return self._peek().type == type

    def _checknext(self, type: TokenType) -> bool:
        """Check if the next token is of the given type."""
        if self.current + 1 >= len(self.tokens):
            return False
        return self.tokens[self.current + 1].type == type

    def _match(self, *types: TokenType) -> bool:
        for type in types:
            if self._check(type):
                self._advance()
                return True
        return False

    def _consume(self, type: TokenType, message: str) -> Token:
        if self._check(type):
            return self._advance()

        raise ParseError(f"{message}. Found {self._peek().type}")

    def _synchronize(self) -> None:
        """Skip tokens until the next statement boundary for error recovery."""
        self._advance()

        while not self._reachedend():
            if self._previous().type == TokenType.EOL:
                return

            if self._peek().type in [
                TokenType.DEFINE,
                TokenType.ASSERT,
                TokenType.BEGIN,
                TokenType.QUERY
            ]:
                return

            self._advance()
