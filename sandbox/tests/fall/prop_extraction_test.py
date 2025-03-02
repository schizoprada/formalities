# ~/formalities/sandbox/tests/fall/prop_extraction_test.py
"""Test script for proposition structure extraction and comparison."""

from formalities.fall.bridges.nlp import NLPBridge
from formalities.fall.bridges.logic import LogicBridge
from formalities.core.types.propositions import AtomicProposition
from loguru import logger as log

def main():
    log.remove()
    """Run tests for proposition structure extraction and comparison."""
    print("\n=== Proposition Structure Extraction Test ===\n")

    # Initialize bridges
    nlp = NLPBridge()
    logic = LogicBridge()

    # Enable NLP bridge
    print(nlp.enable())

    # Test case 1: Extract structure from various propositions
    print("\n--- Proposition Structure Extraction ---")
    propositions = [
        "Socrates is a man",
        "All men are mortal",
        "Socrates is mortal",
        "The sky is blue",
        "Dogs are mammals",
        "All philosophers think deeply"
    ]

    structures = {}
    for text in propositions:
        structure = nlp.extractstructure(text)
        structures[text] = structure
        print(f"\nStructure for: '{text}'")
        print(f"  Subject: {structure.subject}")
        print(f"  Verb: {structure.verb}")
        print(f"  Objects: {structure.objects}")
        print(f"  Modifiers: {structure.modifiers}")

    # Test case 2: Create and compare propositions
    print("\n--- Proposition Creation and Comparison ---")
    logic_props = {}
    for text in propositions:
        name = text.split()[0].lower()  # Use first word as name
        prop = logic.createproposition(name)
        logic_props[text] = prop

        # Add text attribute for NLP bridge to use
        setattr(prop, 'text', text)

        # Add structure attribute
        setattr(prop, 'structure', {"text": text})

        print(f"Created proposition: {name} = '{text}'")

    # Test case 3: Symbolize propositions
    print("\n--- Proposition Symbolization ---")
    for text, prop in logic_props.items():
        symbol = nlp.symbolize(prop)
        print(f"'{text}' symbolized as: {symbol}")

    # Test case 4: Compare proposition pairs
    print("\n--- Proposition Semantic Validation ---")
    proposition_pairs = [
        # Valid syllogism components
        ("Socrates is a man", "All men are mortal"),
        ("All men are mortal", "Socrates is mortal"),
        ("Socrates is a man", "Socrates is mortal"),

        # Invalid combinations
        ("Socrates is a dog", "All men are mortal"),
        ("The sky is blue", "Dogs are mammals"),

        # Edge cases
        ("All men are mortal", "All philosophers think deeply"),
        ("Dogs are mammals", "All philosophers think deeply")
    ]

    for p1_text, p2_text in proposition_pairs:
        p1 = logic_props[p1_text]
        p2 = logic_props[p2_text]

        # Test common token overlap
        overlap, common_tokens = nlp.calctokenoverlap(p1_text, p2_text)
        print(f"\nOverlap between '{p1_text}' and '{p2_text}':")
        print(f"  Score: {overlap:.4f}")
        print(f"  Common tokens: {list(common_tokens)[:10]}")

        # Extract structures
        s1 = structures[p1_text]
        s2 = structures[p2_text]

        # Compare subjects and objects
        if s1.subject and s2.subject:
            subj_sim = nlp.getsimilarity(s1.subject, s2.subject)
            print(f"  Subject similarity ({s1.subject}, {s2.subject}): {subj_sim:.4f}")

        if s1.objects and s2.objects:
            obj_sim = nlp.getsimilarity(s1.objects[0], s2.objects[0])
            print(f"  Object similarity ({s1.objects[0]}, {s2.objects[0]}): {obj_sim:.4f}")

if __name__ == "__main__":
    main()
