# ~/formalities/sandbox/tests/fall/syllogism_proof_test.py
"""Test script for full syllogism proof execution."""

from formalities.fall.parser.lexing import Lexer
from formalities.fall.parser.parsing import Parser
from formalities.fall.runtime.interpreter import Interpreter
from formalities.fall.runtime.executor import ProofExecutor
from formalities.fall.bridges.nlp import NLPBridge
from formalities.fall.bridges.logic import LogicBridge
from loguru import logger as log

def parse_and_execute(fall_code):
    """Parse and execute FALL code."""
    # Lex and parse the code
    lexer = Lexer(fall_code)
    tokens = lexer.scantokens()
    parser = Parser(tokens)
    program = parser.parse()

    # Create interpreter
    interpreter = Interpreter()

    # Enable NLP bridge before interpretation
    bridge = NLPBridge()
    bridge.enable()
    interpreter.environment.bridge.nlpbridge = bridge

    # Interpret the program
    interpreter.interpret(program)

    # Return output
    return interpreter.environment.getoutput()

def main():
    """Run tests for syllogistic proof execution."""
    print("\n=== Full Syllogism Proof Test ===\n")

    # Test case 1: Valid syllogism
    valid_syllogism = """
!- this proof should evaluate as true
BRIDGE NLP ON //

DEFINE PROPOSITION p AS "Socrates is a man" WHERE "Socrates" IS SUBJECT AND "man" IS PREDICATE //

DEFINE PROPOSITION q AS "All men are mortal" WHERE "men" IS SUBJECT AND "mortal" IS PREDICATE //

DEFINE PROPOSITION r AS "Socrates is mortal" WHERE "Socrates" IS SUBJECT AND "mortal" IS PREDICATE //

DEFINE AXIOM Syllogism WHERE p IS TRUE AND q IS TRUE //

BEGIN PROOF
GIVEN p
GIVEN q
PROVE r
USING Syllogism
STEP 1: ASSERT p AND q
STEP 2: INFER r FROM [p, q] VIA Syllogism
END PROOF //

QUERY r //

SYMBOLIZE r //
"""

    print("\n--- Valid Syllogism Test ---")
    result = parse_and_execute(valid_syllogism)
    print(result)

    # Test case 2: Invalid syllogism
    invalid_syllogism = """
!- this proof should evaluate as false
BRIDGE NLP ON //

DEFINE PROPOSITION p AS "Socrates is a dog" WHERE "Socrates" IS SUBJECT AND "dog" IS PREDICATE //

DEFINE PROPOSITION q AS "All men are idiots" WHERE "men" IS SUBJECT AND "idiots" IS PREDICATE //

DEFINE PROPOSITION r AS "Socrates is an idiot" WHERE "Socrates" IS SUBJECT AND "idiots" IS PREDICATE //

DEFINE AXIOM Syllogism WHERE p IS TRUE AND q IS TRUE //

BEGIN PROOF
GIVEN p
GIVEN q
PROVE r
USING Syllogism
STEP 1: ASSERT p AND q
STEP 2: INFER r FROM [p, q] VIA Syllogism
END PROOF //

QUERY r //

SYMBOLIZE r //
"""

    print("\n--- Invalid Syllogism Test ---")
    result = parse_and_execute(invalid_syllogism)
    print(result)

    # Test case 3: Alternative valid syllogism
    alt_valid_syllogism = """
!- Simple valid test
BRIDGE NLP ON //

DEFINE PROPOSITION p AS "Aristotle is a philosopher" WHERE "Aristotle" IS SUBJECT AND "philosopher" IS PREDICATE //

DEFINE PROPOSITION q AS "All philosophers are thinkers" WHERE "philosophers" IS SUBJECT AND "thinkers" IS PREDICATE //

DEFINE PROPOSITION r AS "Aristotle is a thinker" WHERE "Aristotle" IS SUBJECT AND "thinker" IS PREDICATE //

DEFINE AXIOM Syllogism WHERE p IS TRUE AND q IS TRUE //

BEGIN PROOF
GIVEN p
GIVEN q
PROVE r
USING Syllogism
STEP 1: ASSERT p AND q
STEP 2: INFER r FROM [p, q] VIA Syllogism
END PROOF //

QUERY r //
"""

    print("\n--- Alternative Valid Syllogism Test ---")
    result = parse_and_execute(alt_valid_syllogism)
    print(result)

    # Test case 4: Universal instantiation with different phrasing
    universal_instantiation = """
!- Universal instantiation test
BRIDGE NLP ON //

DEFINE PROPOSITION p AS "Plato is human" WHERE "Plato" IS SUBJECT AND "human" IS PREDICATE //

DEFINE PROPOSITION q AS "Humans must die" WHERE "Humans" IS SUBJECT AND "die" IS PREDICATE //

DEFINE PROPOSITION r AS "Plato must die" WHERE "Plato" IS SUBJECT AND "die" IS PREDICATE //

DEFINE AXIOM UniversalInstantiation WHERE p IS TRUE AND q IS TRUE //

BEGIN PROOF
GIVEN p
GIVEN q
PROVE r
USING UniversalInstantiation
STEP 1: ASSERT p AND q
STEP 2: INFER r FROM [p, q] VIA UniversalInstantiation
END PROOF //

QUERY r //
"""

    print("\n--- Universal Instantiation Test ---")
    result = parse_and_execute(universal_instantiation)
    print(result)

if __name__ == "__main__":
    main()
