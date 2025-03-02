# ~/formalities/sandbox/fall/relationship_detection.py
"""Implementation of enhanced relationship detection for NLP Bridge."""

from nltk.corpus import wordnet as wn
from loguru import logger as log

def get_best_synset(term, pos=None):
    """
    Get the best synset for a term, optionally filtering by part of speech.
    Returns None if no synsets are found.
    """
    synsets = wn.synsets(term, pos=pos)
    if not synsets:
        return None

    # Use the most common sense (first synset)
    return synsets[0]

def is_hyponym_of(term1, term2, max_depth=5):
    """
    Check if term1 is a hyponym of term2 (term1 IS-A term2).
    Example: "man" is a hyponym of "person"

    Args:
        term1 (str): The potential hyponym
        term2 (str): The potential hypernym
        max_depth (int): Maximum depth to traverse in the hypernym hierarchy

    Returns:
        tuple: (bool, float) - Whether the relationship exists and its confidence score
    """
    synset1 = get_best_synset(term1)
    synset2 = get_best_synset(term2)

    if not synset1 or not synset2:
        log.debug(f"Could not find synsets for {term1} or {term2}")
        return False, 0.0

    # Check if term2 is a hypernym of term1
    all_hypernyms = set()
    current_level = [synset1]
    depth = 0

    while current_level and depth < max_depth:
        next_level = []
        for synset in current_level:
            direct_hypernyms = synset.hypernyms()
            all_hypernyms.update(direct_hypernyms)
            next_level.extend(direct_hypernyms)

        current_level = next_level
        depth += 1

    # Check if term2's synset is in the hypernym hierarchy of term1
    is_hypernym = synset2 in all_hypernyms

    # Calculate confidence based on path similarity
    confidence = synset1.path_similarity(synset2) or 0.0

    log.debug(f"Hyponym check: {term1} IS-A {term2} = {is_hypernym} (confidence: {confidence:.2f})")
    return is_hypernym, confidence

def is_hypernym_of(term1, term2, max_depth=5):
    """
    Check if term1 is a hypernym of term2 (term2 IS-A term1).
    Example: "person" is a hypernym of "man"

    Args:
        term1 (str): The potential hypernym
        term2 (str): The potential hyponym
        max_depth (int): Maximum depth to traverse in the hypernym hierarchy

    Returns:
        tuple: (bool, float) - Whether the relationship exists and its confidence score
    """
    # Reverse the terms for the hyponym check
    return is_hyponym_of(term2, term1, max_depth)

def are_siblings(term1, term2):
    """
    Check if term1 and term2 are siblings (share a direct common hypernym).
    Example: "man" and "woman" are siblings under "person"

    Returns:
        tuple: (bool, float, str) - Whether they're siblings, confidence, and the common hypernym
    """
    synset1 = get_best_synset(term1)
    synset2 = get_best_synset(term2)

    if not synset1 or not synset2:
        return False, 0.0, None

    # Get immediate hypernyms
    hypernyms1 = set(synset1.hypernyms())
    hypernyms2 = set(synset2.hypernyms())

    # Find common hypernyms
    common_hypernyms = hypernyms1.intersection(hypernyms2)

    if not common_hypernyms:
        return False, 0.0, None

    # Use the "closest" common hypernym (most specific)
    best_hypernym = max(common_hypernyms, key=lambda h: (synset1.path_similarity(h) or 0) + (synset2.path_similarity(h) or 0))
    confidence = min(synset1.path_similarity(best_hypernym) or 0, synset2.path_similarity(best_hypernym) or 0)

    return True, confidence, best_hypernym.name().split('.')[0]

def wu_palmer_similarity(term1, term2):
    """
    Calculate Wu-Palmer similarity between terms.
    This measure considers the depth of the terms in the taxonomy and their least common subsumer.

    Returns:
        float: Similarity score between 0 and 1
    """
    synset1 = get_best_synset(term1)
    synset2 = get_best_synset(term2)

    if not synset1 or not synset2:
        return 0.0

    similarity = synset1.wup_similarity(synset2) or 0.0
    log.debug(f"Wu-Palmer similarity between {term1} and {term2}: {similarity:.4f}")
    return similarity

def determine_relationship_type(premise1_text, premise2_text, conclusion_text=None):
    """
    Determine the type of logical relationship needed based on proposition structure.

    Returns:
        str: The type of relationship ("hyponym", "hypernym", "equivalent", "property", etc.)
    """
    premise1_lower = premise1_text.lower()

    # Check for universal statements like "All X are Y"
    if any(term in premise1_lower for term in ["all", "every", "each"]):
        return "class_inclusion"

    # Check for "X is a Y" statements
    if " is a " in premise1_lower or " is an " in premise1_lower:
        return "instance_of"

    # Check for "X has Y" statements
    if " has " in premise1_lower or " have " in premise1_lower:
        return "property"

    # Default to a general semantic relationship
    return "semantic"

def extract_key_terms(text):
    """
    Extract key terms from text for relationship analysis.

    Returns:
        dict: Dictionary with subject, predicate, etc.
    """
    # Simplified extraction - in a real implementation, use SpaCy's dependency parsing
    parts = text.lower().split(" is ")
    if len(parts) < 2:
        return {"subject": None, "predicate": None}

    subject = parts[0].strip()

    # Handle "is a" construction
    predicate = parts[1].strip()
    if predicate.startswith("a ") or predicate.startswith("an "):
        predicate = predicate[2:].strip()

    return {"subject": subject, "predicate": predicate}

def validate_syllogistic_inference(premise1_text, premise2_text, conclusion_text):
    """
    Validate a syllogistic inference based on the structure of the propositions.

    Example:
        "All men are mortal" (All M are P)
        "Socrates is a man" (S is M)
        "Socrates is mortal" (S is P)

    Returns:
        tuple: (bool, float, str) - Valid, confidence, explanation
    """
    # Extract key terms
    major = extract_key_terms(premise1_text)
    minor = extract_key_terms(premise2_text)
    conclusion = extract_key_terms(conclusion_text)

    log.debug(f"Major premise: {major}")
    log.debug(f"Minor premise: {minor}")
    log.debug(f"Conclusion: {conclusion}")

    # Check for syllogistic pattern (All M are P, S is M, therefore S is P)
    if "all" in premise1_text.lower():
        # Extract middle term (M) and predicate (P) from "All M are P"
        m_term = major["subject"]
        p_term = major["predicate"]

        # Check if minor premise connects subject (S) to middle term (M)
        s_term = minor["subject"]

        # In "S is M", the predicate should match the subject of "All M are P"
        if minor["predicate"] != m_term:
            return False, 0.0, f"Middle term mismatch: '{minor['predicate']}' should match '{m_term}'"

        # Check if conclusion correctly connects S to P
        if conclusion["subject"] != s_term or conclusion["predicate"] != p_term:
            return False, 0.0, f"Conclusion mismatch: should be '{s_term} is {p_term}'"

        # If structure is valid, check semantic relationships
        term_match, confidence = is_hyponym_of(s_term, m_term)

        if not term_match:
            return False, confidence, f"'{s_term}' is not a type of '{m_term}'"

        # Valid syllogism
        return True, confidence, f"Valid syllogism: '{s_term}' is a type of '{m_term}', and all '{m_term}' are '{p_term}'"

    # Handle other syllogistic forms here

    return False, 0.0, "Unsupported syllogistic pattern"

# Demo function for testing
def test_relationships():
    """
    Test the relationship detection functions with some examples.
    """
    print("\n=== Testing Enhanced Relationship Detection ===\n")

    # Test hyponym/hypernym relationships
    term_pairs = [
        ("man", "person"),
        ("dog", "mammal"),
        ("human", "mortal"),
        ("Socrates", "philosopher"),
        ("dog", "person"),  # Should be False
        ("idiot", "person")
    ]

    print("--- Hyponym Relationships (X IS-A Y) ---")
    for term1, term2 in term_pairs:
        is_hypo, confidence = is_hyponym_of(term1, term2)
        print(f"'{term1}' IS-A '{term2}': {is_hypo} (confidence: {confidence:.2f})")

    print("\n--- Hypernym Relationships (Y IS-A X) ---")
    for term1, term2 in term_pairs:
        is_hyper, confidence = is_hypernym_of(term1, term2)
        print(f"'{term2}' IS-A '{term1}': {is_hyper} (confidence: {confidence:.2f})")

    print("\n--- Wu-Palmer Similarity ---")
    for term1, term2 in term_pairs:
        similarity = wu_palmer_similarity(term1, term2)
        print(f"Similarity({term1}, {term2}) = {similarity:.4f}")

    print("\n--- Sibling Relationships ---")
    sibling_pairs = [
        ("man", "woman"),
        ("dog", "cat"),
        ("apple", "orange"),
        ("car", "truck"),
        ("Socrates", "Plato")
    ]

    for term1, term2 in sibling_pairs:
        is_sib, confidence, common = are_siblings(term1, term2)
        result = f"'{common}'" if common else "None"
        print(f"'{term1}' and '{term2}' are siblings: {is_sib} (confidence: {confidence:.2f}, common parent: {result})")

    print("\n--- Syllogistic Validation ---")
    syllogisms = [
        # Valid syllogism
        (
            "All men are mortal",
            "Socrates is a man",
            "Socrates is mortal"
        ),
        # Invalid syllogism
        (
            "All men are mortal",
            "Socrates is a dog",
            "Socrates is mortal"
        ),
        # Valid but different domain
        (
            "All philosophers are thinkers",
            "Aristotle is a philosopher",
            "Aristotle is a thinker"
        )
    ]

    for major, minor, conclusion in syllogisms:
        valid, confidence, reason = validate_syllogistic_inference(major, minor, conclusion)
        print(f"\nSyllogism:")
        print(f"  Major: {major}")
        print(f"  Minor: {minor}")
        print(f"  Conclusion: {conclusion}")
        print(f"  Valid: {valid} (confidence: {confidence:.2f})")
        print(f"  Reason: {reason}")

if __name__ == "__main__":
    test_relationships()
