# ~/formalities/sandbox/tests/fall/language_processing.py
from formalities.fall.core.types.language.common import (
    WordType, WordFunction, RelationshipType, StatementType
)
from formalities.fall.core.types.language.base import Word, Statement
from formalities.fall.core.types.language.syllogistic import (
    Syllogism, SyllogisticProcessor, ValidationResultStatus
)
from loguru import logger as log

def test_word_processing():
    """Test Word class functionality."""
    print("\n=== Testing Word Processing ===")

    words = [
        "Socrates",  # Proper noun
        "man",       # Noun
        "mortal",    # Adjective
        "is",        # Copula
        "all",       # Quantifier
        "the"        # Article
    ]

    for word_text in words:
        word = Word(word_text)
        print(f"Word: {word.content}")
        print(f"  Type: {word.type.name}")
        print(f"  Lemma: {word.lemma}")
        print()

def test_statement_processing():
    """Test Statement class functionality."""
    print("\n=== Testing Statement Processing ===")

    statements = [
        "Socrates is a man",
        "All men are mortal",
        "Socrates is mortal",
        "All philosophers are thinkers",
        "Aristotle is a philosopher",
        "Some birds can fly",
        "No fish are mammals"
    ]

    for statement_text in statements:
        statement = Statement(statement_text)
        print(f"Statement: '{statement.content}'")
        print(f"  Type: {statement.type.name}")
        print(f"  Relationships: {[r.name for r in statement._relationships]}")
        print("  Words:")

        for word in statement._words:
            func_str = word.function.name if word.function else "UNKNOWN"
            print(f"    '{word.content}': {word.type.name}, function={func_str}")

        if statement.subjects:
            print(f"  Subject: {[w.content for w in statement.subjects]}")
        if statement.predicates:
            print(f"  Predicate: {[w.content for w in statement.predicates]}")
        if statement.predicatenominatives:
            print(f"  Predicate Nominative: {[w.content for w in statement.predicatenominatives]}")
        if statement.predicateadjectives:
            print(f"  Predicate Adjective: {[w.content for w in statement.predicateadjectives]}")
        if statement.copuli:
            print(f"  Copula: {[w.content for w in statement.copuli]}")
        print()

def test_syllogism_processing():
    """Test syllogistic reasoning."""
    print("\n=== Testing Syllogistic Reasoning ===")

    # Test case 1: Valid syllogism
    syllogism1_text = """
    All men are mortal.
    Socrates is a man.
    Socrates is mortal.
    """

    # Test case 2: Invalid structure - wrong conclusion subject
    syllogism2_text = """
    All men are mortal.
    Socrates is a man.
    Plato is mortal.
    """

    # Test case 3: Invalid structure - wrong conclusion predicate
    syllogism3_text = """
    All men are mortal.
    Socrates is a man.
    Socrates is a philosopher.
    """

    # Test case 4: Invalid semantics - wrong minor premise relationship
    syllogism4_text = """
    All men are mortal.
    Socrates is mortal.
    Socrates is mortal.
    """

    # Test case 5: Invalid semantics - wrong major premise relationship
    syllogism5_text = """
    Men are mortal.
    Socrates is a man.
    Socrates is mortal.
    """

    # Test case 6: Valid syllogism with different terms
    syllogism6_text = """
    All philosophers are thinkers.
    Aristotle is a philosopher.
    Aristotle is a thinker.
    """

    test_cases = [
        ("Valid Classic Syllogism", syllogism1_text),
        ("Invalid - Wrong Conclusion Subject", syllogism2_text),
        ("Invalid - Wrong Conclusion Predicate", syllogism3_text),
        ("Invalid - Wrong Minor Premise Relationship", syllogism4_text),
        ("Invalid - Wrong Major Premise Type", syllogism5_text),
        ("Valid Philosophy Syllogism", syllogism6_text)
    ]

    for case_name, syllogism_text in test_cases:
        print(f"\n--- {case_name} ---")
        print(syllogism_text.strip())

        try:
            syllogism = SyllogisticProcessor.ProcessSyllogisticBody(syllogism_text)
            print(f"Valid: {syllogism.isvalid}")
            print(f"Form: {syllogism.form}")
            print(f"Validation Message: {syllogism.validationmessage}")
        except Exception as e:
            print(f"Error processing syllogism: {e}")

def test_custom_syllogism(major_premise, minor_premise, conclusion):
    """Test a custom syllogism provided by the user."""
    print("\n=== Testing Custom Syllogism ===")
    print(f"Major Premise: {major_premise}")
    print(f"Minor Premise: {minor_premise}")
    print(f"Conclusion: {conclusion}")

    try:
        syllogism = SyllogisticProcessor.ProcessSyllogism(
            major_premise, minor_premise, conclusion
        )
        print(f"Valid: {syllogism.isvalid}")
        print(f"Form: {syllogism.form}")
        print(f"Validation Message: {syllogism.validationmessage}")

        # Print more detailed information
        print("\nMajor Premise Analysis:")
        mp = syllogism.majorpremise
        print(f"  Type: {mp.type.name}")
        print(f"  Relationships: {[r.name for r in mp._relationships]}")
        print(f"  Subject: {[w.content for w in mp.subjects]}")

        if mp.predicates:
            print(f"  Predicate: {[w.content for w in mp.predicates]}")
        if mp.predicatenominatives:
            print(f"  Predicate Nominative: {[w.content for w in mp.predicatenominatives]}")
        if mp.predicateadjectives:
            print(f"  Predicate Adjective: {[w.content for w in mp.predicateadjectives]}")

        print("\nMinor Premise Analysis:")
        mi = syllogism.minorpremise
        print(f"  Type: {mi.type.name}")
        print(f"  Relationships: {[r.name for r in mi._relationships]}")
        print(f"  Subject: {[w.content for w in mi.subjects]}")

        if mi.predicates:
            print(f"  Predicate: {[w.content for w in mi.predicates]}")
        if mi.predicatenominatives:
            print(f"  Predicate Nominative: {[w.content for w in mi.predicatenominatives]}")
        if mi.predicateadjectives:
            print(f"  Predicate Adjective: {[w.content for w in mi.predicateadjectives]}")

        print("\nConclusion Analysis:")
        c = syllogism.conclusion
        print(f"  Type: {c.type.name}")
        print(f"  Relationships: {[r.name for r in c._relationships]}")
        print(f"  Subject: {[w.content for w in c.subjects]}")

        if c.predicates:
            print(f"  Predicate: {[w.content for w in c.predicates]}")
        if c.predicatenominatives:
            print(f"  Predicate Nominative: {[w.content for w in c.predicatenominatives]}")
        if c.predicateadjectives:
            print(f"  Predicate Adjective: {[w.content for w in c.predicateadjectives]}")

    except Exception as e:
        print(f"Error processing custom syllogism: {e}")

def main():
    log.remove()
    """Run all tests."""
    print("=== Language Processing and Syllogistic Reasoning Tests ===")

    # Test word processing
    test_word_processing()

    # Test statement processing
    test_statement_processing()

    # Test syllogistic reasoning
    test_syllogism_processing()

    # Test a custom syllogism (classic example)
    test_custom_syllogism(
        "All men are mortal",
        "Socrates is a man",
        "Socrates is mortal"
    )

    # Test another custom syllogism
    test_custom_syllogism(
        "All mammals are warm-blooded",
        "Whales are mammals",
        "Whales are warm-blooded"
    )

if __name__ == "__main__":
    main()
