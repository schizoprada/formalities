# ~/formalities/sandbox/tests/fall/infer_val_test.py
"""Test script for inference validation with NLP Bridge."""

from formalities.fall.bridges.nlp import NLPBridge
from formalities.fall.bridges.logic import LogicBridge
from formalities.core.types.propositions import AtomicProposition
from loguru import logger as log

def main():
    """Run tests for inference validation."""
    print("\n=== Inference Validation Test ===\n")

    # Initialize bridges
    nlp = NLPBridge()
    logic = LogicBridge()

    # Connect NLP Bridge to Logic Bridge
    logic.nlpbridge = nlp

    # Enable NLP bridge
    print(nlp.enable())
    print(f"Current similarity threshold: {nlp.simthresh}")

    # Test case 1: Valid syllogism
    print("\n--- Valid Syllogism ---")
    test_valid_syllogism(nlp, logic)

    # Test case 2: Invalid syllogism
    print("\n--- Invalid Syllogism ---")
    test_invalid_syllogism(nlp, logic)

    # Test case 3: Edge cases
    print("\n--- Edge Cases ---")
    test_edge_cases(nlp, logic)

    # Test case 4: Threshold sensitivity
    print("\n--- Threshold Sensitivity ---")
    test_threshold_sensitivity(nlp, logic)

def test_valid_syllogism(nlp, logic):
    """Test valid syllogistic reasoning."""
    # Create premises and conclusion
    p1 = logic.createproposition("p")
    setattr(p1, 'text', "Socrates is a man")

    p2 = logic.createproposition("q")
    setattr(p2, 'text', "All men are mortal")

    conclusion = logic.createproposition("r")
    setattr(conclusion, 'text', "Socrates is mortal")

    # Extract structures
    for prop in [p1, p2, conclusion]:
        structure = nlp.extractstructure(prop.text)
        print(f"Structure for '{prop.text}':")
        print(f"  Subject: {structure.subject}")
        print(f"  Objects: {structure.objects}")

    # Validate inference
    result = nlp.validateinference([p1, p2], conclusion)

    print("\nValidation result:")
    print(f"  Valid: {result.valid}")
    print(f"  Confidence: {result.confidence:.4f}")
    print(f"  Reason: {result.reason}")
    print(f"  Common tokens: {list(result.commontokens)[:10]}")

    # Print detailed connections
    print("\nSemantic connections:")
    for source, target, score in result.connections:
        if score >= nlp.simthresh:
            status = "PASS"
        else:
            status = "FAIL"
        print(f"  {source} - {target}: {score:.4f} [{status}]")

def test_invalid_syllogism(nlp, logic):
    """Test invalid syllogistic reasoning."""
    # Create premises and conclusion
    p1 = logic.createproposition("p")
    setattr(p1, 'text', "Socrates is a dog")

    p2 = logic.createproposition("q")
    setattr(p2, 'text', "All men are mortal")

    conclusion = logic.createproposition("r")
    setattr(conclusion, 'text', "Socrates is mortal")

    # Validate inference
    result = nlp.validateinference([p1, p2], conclusion)

    print("\nValidation result:")
    print(f"  Valid: {result.valid}")
    print(f"  Confidence: {result.confidence:.4f}")
    print(f"  Reason: {result.reason}")
    print(f"  Common tokens: {list(result.commontokens)[:10]}")

    # Print detailed connections
    print("\nSemantic connections:")
    for source, target, score in result.connections:
        if score >= nlp.simthresh:
            status = "PASS"
        else:
            status = "FAIL"
        print(f"  {source} - {target}: {score:.4f} [{status}]")

def test_edge_cases(nlp, logic):
    """Test edge cases for inference validation."""
    # Test case 1: Similar subject, different predicate
    p1 = logic.createproposition("p")
    setattr(p1, 'text', "Socrates is a philosopher")

    p2 = logic.createproposition("q")
    setattr(p2, 'text', "All men are mortal")

    conclusion = logic.createproposition("r")
    setattr(conclusion, 'text', "Socrates is mortal")

    result = nlp.validateinference([p1, p2], conclusion)
    print("\nTest: Philosopher → Mortal")
    print(f"  Valid: {result.valid}")
    print(f"  Confidence: {result.confidence:.4f}")
    print(f"  Reason: {result.reason}")

    # Test case 2: Different domain
    p1 = logic.createproposition("p")
    setattr(p1, 'text', "The sky is blue")

    p2 = logic.createproposition("q")
    setattr(p2, 'text', "All blue things are cold")

    conclusion = logic.createproposition("r")
    setattr(conclusion, 'text', "The sky is cold")

    result = nlp.validateinference([p1, p2], conclusion)
    print("\nTest: Sky → Blue → Cold")
    print(f"  Valid: {result.valid}")
    print(f"  Confidence: {result.confidence:.4f}")
    print(f"  Reason: {result.reason}")

def test_threshold_sensitivity(nlp, logic):
    """Test sensitivity to similarity threshold."""
    # Create a borderline valid inference
    p1 = logic.createproposition("p")
    setattr(p1, 'text', "Plato is a philosopher")

    p2 = logic.createproposition("q")
    setattr(p2, 'text', "All thinkers are wise")

    conclusion = logic.createproposition("r")
    setattr(conclusion, 'text', "Plato is wise")

    # Test with different thresholds
    thresholds = [0.4, 0.5, 0.6, 0.7, 0.8]
    original_threshold = nlp.simthresh

    for threshold in thresholds:
        nlp.setsimthresh(threshold)
        result = nlp.validateinference([p1, p2], conclusion)
        print(f"\nThreshold {threshold:.2f}:")
        print(f"  Valid: {result.valid}")
        print(f"  Confidence: {result.confidence:.4f}")
        print(f"  Reason: {result.reason}")

    # Restore original threshold
    nlp.simthresh = original_threshold

if __name__ == "__main__":
    main()
