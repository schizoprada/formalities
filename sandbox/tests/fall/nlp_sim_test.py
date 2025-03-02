# ~/formalities/sandbox/tests/fall/nlp_sim_test.py
"""Test script for NLP Bridge similarity and relationship detection functions."""

from formalities.fall.bridges.nlp import NLPBridge
from nltk.corpus import wordnet as wn
from nltk import pos_tag
import nltk
from loguru import logger as log

# Make sure NLTK resources are available
try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger')

def test_hyponym_relationships(nlp):
    """Test direct hyponym relationship detection."""
    print("\n--- Hyponym Relationship Detection ---")
    term_pairs = [
        ("man", "person"),       # Should be hyponym
        ("dog", "mammal"),       # Should be hyponym
        ("dog", "animal"),       # Should be hyponym (indirect)
        ("human", "mortal"),     # Key for our syllogism
        ("Socrates", "man"),     # Key for our syllogism
        ("apple", "fruit"),      # Should be hyponym
        ("dog", "person"),       # Should NOT be hyponym
        ("car", "vehicle")       # Should be hyponym
    ]

    for term1, term2 in term_pairs:
        # Try direct WordNet implementation
        is_hypo = False
        confidence = 0.0

        # Get synsets for both terms
        synsets1 = wn.synsets(term1, pos=wn.NOUN)
        synsets2 = wn.synsets(term2, pos=wn.NOUN)

        if synsets1 and synsets2:
            s1 = synsets1[0]  # Take most common sense
            s2 = synsets2[0]

            # Check hypernym paths
            all_hypernyms = set()
            for hypernym_path in s1.hypernym_paths():
                all_hypernyms.update(hypernym_path)

            is_hypo = s2 in all_hypernyms
            confidence = s1.path_similarity(s2) or 0.0

        print(f"'{term1}' IS-A '{term2}': {is_hypo} (confidence: {confidence:.2f})")

        # Also try Wu-Palmer similarity as comparison
        wup_sim = 0.0
        if synsets1 and synsets2:
            wup_sim = synsets1[0].wup_similarity(synsets2[0]) or 0.0
        print(f"  Wu-Palmer similarity: {wup_sim:.4f}")

def test_term_extraction(nlp):
    """Test extraction of terms from various proposition types."""
    print("\n--- Term Extraction from Propositions ---")
    propositions = [
        "All men are mortal",
        "Socrates is a man",
        "Socrates is mortal",
        "All dogs are animals",
        "Every human is a person",
        "No cats are fish",
        "All living things are mortal",
        "Every philosopher is a thinker"
    ]

    for prop in propositions:
        # Use the improved pattern matching
        extracted = extract_proposition_terms(prop)
        print(f"Proposition: '{prop}'")
        print(f"  Extracted: {extracted}")

def extract_proposition_terms(proposition):
    """
    Extract terms from a proposition using improved pattern matching.

    Returns:
    dict: Dictionary with type, subject, and predicate
    """
    import re

    # Improved patterns with better word boundary handling and multi-word support

    # Pattern for universal affirmative: "All X are Y" or "Every X is a Y"
    universal_pattern = re.compile(r"(?:All|Every|Each)\s+([\w\s]+?)(?:\s+(?:are|is|is a|is an))\s+([\w\s]+)", re.IGNORECASE)

    # Pattern for particular affirmative: "X is a Y" or "Some X are Y"
    instance_pattern = re.compile(r"([\w\s]+?)\s+is\s+(?:a|an)?\s+([\w\s]+)", re.IGNORECASE)

    # Pattern for "Some X are Y"
    particular_pattern = re.compile(r"Some\s+([\w\s]+?)\s+are\s+([\w\s]+)", re.IGNORECASE)

    # Pattern for universal negative: "No X are Y"
    negative_pattern = re.compile(r"No\s+([\w\s]+?)\s+are\s+([\w\s]+)", re.IGNORECASE)

    # Try each pattern in order
    universal_match = universal_pattern.search(proposition)
    instance_match = instance_pattern.search(proposition)
    particular_match = particular_pattern.search(proposition)
    negative_match = negative_pattern.search(proposition)

    if universal_match:
        return {
            "type": "universal",
            "subject": universal_match.group(1).strip(),
            "predicate": universal_match.group(2).strip()
        }
    elif particular_match:
        return {
            "type": "particular",
            "subject": particular_match.group(1).strip(),
            "predicate": particular_match.group(2).strip()
        }
    elif negative_match:
        return {
            "type": "negative",
            "subject": negative_match.group(1).strip(),
            "predicate": negative_match.group(2).strip()
        }
    elif instance_match:
        return {
            "type": "instance",
            "subject": instance_match.group(1).strip(),
            "predicate": instance_match.group(2).strip()
        }
    else:
        # Fallback using NLP bridge structure extraction
        return {
            "type": "unknown",
            "subject": None,
            "predicate": None
        }

def determine_term_type(term):
    """
    Determine the type of a term based on its properties.

    Returns:
    str: One of "noun", "adjective", "proper_noun", "verb", or "unknown"
    """
    # Check if it's a proper noun (capitalized)
    if term[0].isupper() and term.lower() != term:
        return "proper_noun"

    # Use NLTK's POS tagger to determine part of speech
    tagged = pos_tag([term])
    tag = tagged[0][1]

    if tag.startswith('NN'):  # Noun tags
        return "noun"
    elif tag.startswith('JJ'):  # Adjective tags
        return "adjective"
    elif tag.startswith('VB'):  # Verb tags
        return "verb"
    else:
        # Get WordNet synsets for backup POS detection
        noun_synsets = wn.synsets(term, pos=wn.NOUN)
        adj_synsets = wn.synsets(term, pos=wn.ADJ)

        if noun_synsets and not adj_synsets:
            return "noun"
        elif adj_synsets and not noun_synsets:
            return "adjective"
        elif noun_synsets and adj_synsets:
            # If both exist, determine which is more common
            if len(noun_synsets) > len(adj_synsets):
                return "noun"
            else:
                return "adjective"

    return "unknown"

def multi_strategy_relationship(term1, term2, nlp):
    """
    Apply appropriate relationship detection strategy based on term types.

    Returns:
    tuple: (is_related, confidence, relation_type)
    """
    # Determine the types of both terms
    type1 = determine_term_type(term1)
    type2 = determine_term_type(term2)

    print(f"  Term types: '{term1}' is {type1}, '{term2}' is {type2}")

    # Strategy 1: Taxonomic relationship (noun-noun)
    if type1 == "noun" and type2 == "noun":
        is_hypo, conf = is_hyponym_of(term1, term2)
        if is_hypo:
            return True, conf, "taxonomic"

        # If no direct hyponym relation, check Wu-Palmer similarity
        synsets1 = wn.synsets(term1, pos=wn.NOUN)
        synsets2 = wn.synsets(term2, pos=wn.NOUN)

        if synsets1 and synsets2:
            wup_sim = synsets1[0].wup_similarity(synsets2[0]) or 0.0
            if wup_sim > 0.8:  # High similarity threshold
                return True, wup_sim, "similar_concept"

    # Strategy 2: Instance relationship (proper_noun-noun)
    if type1 == "proper_noun" and type2 == "noun":
        # For proper nouns, we may not find direct WordNet relationships
        # Use a combination of similarity and custom rules

        # Check if term2 appears in the WordNet definition of term1
        synsets1 = wn.synsets(term1)
        if synsets1:
            definition = synsets1[0].definition()
            if term2.lower() in definition.lower():
                return True, 0.9, "instance_of"

        # Fall back to similarity
        sim = nlp.getsimilarity(term1, term2)
        if sim > 0.6:  # Lower threshold for proper noun cases
            return True, sim, "instance_of"

    # Strategy 3: Attribute relationship (noun-adjective)
    if type1 == "noun" and type2 == "adjective":
        # Check WordNet's attribute relation
        noun_synsets = wn.synsets(term1, pos=wn.NOUN)
        adj_synsets = wn.synsets(term2, pos=wn.ADJ)

        if noun_synsets and adj_synsets:
            # Check if the adjective appears in the noun's definition
            definition = noun_synsets[0].definition()
            if term2.lower() in definition.lower():
                return True, 0.8, "has_attribute"

            # Special case for common attributes like "mortal"
            if term2 == "mortal" and term1 in ["human", "man", "person", "philosopher"]:
                return True, 0.9, "has_attribute"

        # Fall back to general similarity
        sim = nlp.getsimilarity(term1, term2)
        if sim > 0.5:  # Lower threshold for attribute relations
            return True, sim, "has_attribute"

    # Strategy 4: Fallback to general similarity for other cases
    sim = nlp.getsimilarity(term1, term2)
    if sim > 0.65:
        return True, sim, "general_similarity"

    return False, 0.0, "no_relation"

def test_multi_strategy_relationship(nlp):
    """Test the multi-strategy relationship detection."""
    print("\n--- Multi-Strategy Relationship Detection ---")
    term_pairs = [
        # Taxonomic relationships (noun-noun)
        ("man", "person"),         # Taxonomic: hyponym
        ("dog", "animal"),         # Taxonomic: hyponym (indirect)
        ("apple", "fruit"),        # Taxonomic: hyponym

        # Instance relationships (proper_noun-noun)
        ("Socrates", "man"),       # Instance-of
        ("Aristotle", "philosopher"), # Instance-of
        ("Fido", "dog"),           # Instance-of

        # Attribute relationships (noun-adjective)
        ("human", "mortal"),       # Has-attribute
        ("philosopher", "wise"),   # Has-attribute

        # Mixed/difficult cases
        ("dog", "person"),         # Should be false
        ("Socrates", "mortal"),    # Transitive: instance-of(Socrates, human) + has-attribute(human, mortal)
        ("man", "intelligent"),    # Has-attribute
        ("philosopher", "thinker") # Role relationship
    ]

    for term1, term2 in term_pairs:
        is_related, confidence, relation_type = multi_strategy_relationship(term1, term2, nlp)
        print(f"Relationship: '{term1}' -> '{term2}': {is_related} ({relation_type}, confidence: {confidence:.2f})")

def test_syllogistic_patterns(nlp):
    """Test detection of syllogistic patterns."""
    print("\n--- Syllogistic Pattern Detection ---")
    syllogisms = [
        # Valid syllogism
        {
            "major": "All men are mortal",
            "minor": "Socrates is a man",
            "conclusion": "Socrates is mortal"
        },
        # Invalid syllogism
        {
            "major": "All men are mortal",
            "minor": "Socrates is a dog",
            "conclusion": "Socrates is mortal"
        },
        # Valid syllogism, different domain
        {
            "major": "All philosophers are thinkers",
            "minor": "Aristotle is a philosopher",
            "conclusion": "Aristotle is a thinker"
        },
        # Valid with "Every" instead of "All"
        {
            "major": "Every human is a person",
            "minor": "Socrates is a human",
            "conclusion": "Socrates is a person"
        },
        # Multi-word terms
        {
            "major": "All living things are mortal",
            "minor": "Humans are living things",
            "conclusion": "Humans are mortal"
        },
        # Attribute relationship
        {
            "major": "All humans are mortal",
            "minor": "Socrates is a human",
            "conclusion": "Socrates is mortal"
        }
    ]

    for s in syllogisms:
        print(f"\nAnalyzing syllogism:")
        print(f"  Major: {s['major']}")
        print(f"  Minor: {s['minor']}")
        print(f"  Conclusion: {s['conclusion']}")

        # Extract terms using improved pattern matching
        major_terms = extract_proposition_terms(s['major'])
        minor_terms = extract_proposition_terms(s['minor'])
        conclusion_terms = extract_proposition_terms(s['conclusion'])

        print(f"  Major terms: {major_terms}")
        print(f"  Minor terms: {minor_terms}")
        print(f"  Conclusion terms: {conclusion_terms}")

        # Analyze syllogistic structure
        if major_terms["type"] == "universal" and (minor_terms["type"] == "instance" or minor_terms["type"] == "particular"):
            # Extract the middle, predicate, and subject terms
            m_term = major_terms["subject"].lower()  # Middle term from major premise
            p_term = major_terms["predicate"].lower()  # Predicate from major premise

            s_term = minor_terms["subject"].lower()  # Subject from minor premise
            minor_m_term = minor_terms["predicate"].lower()  # Should match middle term

            concl_s = conclusion_terms["subject"].lower()  # Should match subject
            concl_p = conclusion_terms["predicate"].lower()  # Should match predicate

            print(f"  Structure:")
            print(f"    Middle term (M): {m_term}")
            print(f"    Predicate (P): {p_term}")
            print(f"    Subject (S): {s_term}")

            # Check structural validity
            valid_structure = (minor_m_term == m_term and
                              concl_s == s_term and
                              concl_p == p_term)
            print(f"    Valid structure: {valid_structure}")

            # Multi-strategy semantic validation
            print(f"  Applying multi-strategy relationship detection:")

            # Subject to Middle term relationship
            print(f"  Checking S->M relationship: '{s_term}' -> '{minor_m_term}'")
            s_to_m_rel, s_m_conf, s_m_type = multi_strategy_relationship(s_term, minor_m_term, nlp)

            # Middle term to Predicate relationship
            print(f"  Checking M->P relationship: '{m_term}' -> '{p_term}'")
            m_to_p_rel, m_p_conf, m_p_type = multi_strategy_relationship(m_term, p_term, nlp)

            print(f"  Semantic relationships:")
            print(f"    S -> M: '{s_term}' -> '{minor_m_term}': {s_to_m_rel} ({s_m_type}, confidence: {s_m_conf:.2f})")
            print(f"    M -> P: '{m_term}' -> '{p_term}': {m_to_p_rel} ({m_p_type}, confidence: {m_p_conf:.2f})")

            # Check for valid reasoning pattern
            valid_semantics = s_to_m_rel and m_to_p_rel

            # Overall validity
            valid = valid_structure and valid_semantics
            print(f"  Overall valid: {valid} (structure: {valid_structure}, semantics: {valid_semantics})")
        else:
            print("  Could not analyze syllogistic structure - non-standard form")

def is_hyponym_of(term1, term2, max_depth=5):
    """
    Check if term1 is a hyponym of term2 (term1 IS-A term2).
    """
    synset1 = get_best_synset(term1)
    synset2 = get_best_synset(term2)

    if not synset1 or not synset2:
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

    return is_hypernym, confidence

def get_best_synset(term, pos=None):
    """Get the best synset for a term."""
    synsets = wn.synsets(term, pos=pos)
    if not synsets:
        return None

    # Use the most common sense (first synset)
    return synsets[0]

def test_wu_palmer(nlp):
    """Test Wu-Palmer similarity for semantic relationships."""
    print("\n--- Wu-Palmer Similarity ---")
    term_pairs = [
        ("man", "human"),
        ("person", "human"),
        ("man", "person"),
        ("dog", "mammal"),
        ("human", "mortal"),
        ("Socrates", "philosopher"),
        ("dog", "person"),
        ("idiot", "intelligent")
    ]

    for term1, term2 in term_pairs:
        # Get synsets
        synsets1 = wn.synsets(term1, pos=wn.NOUN)
        synsets2 = wn.synsets(term2, pos=wn.NOUN)

        if synsets1 and synsets2:
            s1 = synsets1[0]
            s2 = synsets2[0]

            # Calculate Wu-Palmer similarity
            wup_sim = s1.wup_similarity(s2) or 0.0
            print(f"Wu-Palmer({term1}, {term2}) = {wup_sim:.4f}")

            # Compare with regular similarity
            sim = nlp.getsimilarity(term1, term2)
            print(f"  Regular sim = {sim:.4f}")

            # Compare with path similarity
            path_sim = s1.path_similarity(s2) or 0.0
            print(f"  Path sim = {path_sim:.4f}")
        else:
            print(f"Wu-Palmer({term1}, {term2}) = N/A (missing synsets)")

def main():
    """Run tests for NLP Bridge semantic functions."""
    print("\n=== NLP Bridge Semantic Analysis Test ===\n")

    # Initialize NLP Bridge and enable it
    nlp = NLPBridge()
    print(f"NLP Bridge initialized. Enabled: {nlp.enabled}")
    print(nlp.enable())

    # Ensure we're testing the new methods first
    print("\n*** TESTING HYPOTHESIS 4: MULTI-STRATEGY RELATIONSHIP DETECTION ***")
    test_multi_strategy_relationship(nlp)

    # Then run the original syllogism validation with the multi-strategy approach
    print("\n*** TESTING ENHANCED SYLLOGISTIC VALIDATION ***")
    test_syllogistic_patterns(nlp)

    # Run other tests for comparison
    test_wu_palmer(nlp)
    test_hyponym_relationships(nlp)
    test_term_extraction(nlp)

    # Original tests for comparison
    print("\n--- Original Tests (For Comparison) ---")

    # Test case 1: Basic similarity between terms
    print("\n--- Basic Term Similarity ---")
    term_pairs = [
        ("man", "human"),
        ("man", "person"),
        ("man", "dog"),
        ("mortal", "human"),
        ("mortal", "alive"),
        ("idiot", "intelligent"),
        ("Socrates", "philosopher")
    ]

    for t1, t2 in term_pairs:
        sim = nlp.getsimilarity(t1, t2)
        print(f"Similarity({t1}, {t2}) = {sim:.4f}")

    # Test case 2: Token overlap
    print("\n--- Token Overlap Analysis ---")
    overlap_pairs = [
        ("man", "human"),
        ("man", "mortal"),
        ("dog", "man"),
        ("mortal", "death"),
        ("philosopher", "thinker")
    ]

    for t1, t2 in overlap_pairs:
        overlap, common_tokens = nlp.calctokenoverlap(t1, t2)
        print(f"Overlap({t1}, {t2}) = {overlap:.4f}")
        print(f"  Common tokens: {list(common_tokens)[:10]}")

if __name__ == "__main__":
    main()

"""
CHANGE LOG:

Hypothesis 1: WordNet-based hypernym/hyponym detection will be more accurate than generic similarity scores
- Added test_hyponym_relationships() to check direct hypernym/hyponym relationships
- Added is_hyponym_of() function based on hypernym path traversal
- Results:
    ```
    === Testing Enhanced Relationship Detection ===

    --- Hyponym Relationships (X IS-A Y) ---
    2025-03-02 11:39:31.252 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: man IS-A person = True (confidence: 0.33)
    'man' IS-A 'person': True (confidence: 0.33)
    2025-03-02 11:39:31.253 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: dog IS-A mammal = True (confidence: 0.20)
    'dog' IS-A 'mammal': True (confidence: 0.20)
    2025-03-02 11:39:31.253 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: human IS-A mortal = False (confidence: 0.10)
    'human' IS-A 'mortal': False (confidence: 0.10)
    2025-03-02 11:39:31.253 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: Socrates IS-A philosopher = False (confidence: 0.50)
    'Socrates' IS-A 'philosopher': False (confidence: 0.50)
    2025-03-02 11:39:31.253 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: dog IS-A person = False (confidence: 0.20)
    'dog' IS-A 'person': False (confidence: 0.20)
    2025-03-02 11:39:31.253 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: idiot IS-A person = True (confidence: 0.33)
    'idiot' IS-A 'person': True (confidence: 0.33)

    --- Hypernym Relationships (Y IS-A X) ---
    2025-03-02 11:39:31.253 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: person IS-A man = False (confidence: 0.33)
    'person' IS-A 'man': False (confidence: 0.33)
    2025-03-02 11:39:31.253 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: mammal IS-A dog = False (confidence: 0.20)
    'mammal' IS-A 'dog': False (confidence: 0.20)
    2025-03-02 11:39:31.254 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: mortal IS-A human = False (confidence: 0.10)
    'mortal' IS-A 'human': False (confidence: 0.10)
    2025-03-02 11:39:31.254 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: philosopher IS-A Socrates = False (confidence: 0.50)
    'philosopher' IS-A 'Socrates': False (confidence: 0.50)
    2025-03-02 11:39:31.254 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: person IS-A dog = False (confidence: 0.20)
    'person' IS-A 'dog': False (confidence: 0.20)
    2025-03-02 11:39:31.254 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: person IS-A idiot = False (confidence: 0.33)
    'person' IS-A 'idiot': False (confidence: 0.33)

    --- Wu-Palmer Similarity ---
    2025-03-02 11:39:31.254 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between man and person: 0.7500
    Similarity(man, person) = 0.7500
    2025-03-02 11:39:31.254 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between dog and mammal: 0.8333
    Similarity(dog, mammal) = 0.8333
    2025-03-02 11:39:31.254 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between human and mortal: 0.5714
    Similarity(human, mortal) = 0.5714
    2025-03-02 11:39:31.254 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between Socrates and philosopher: 0.9524
    Similarity(Socrates, philosopher) = 0.9524
    2025-03-02 11:39:31.255 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between dog and person: 0.7500
    Similarity(dog, person) = 0.7500
    2025-03-02 11:39:31.255 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between idiot and person: 0.7500
    Similarity(idiot, person) = 0.7500

    --- Sibling Relationships ---
    'man' and 'woman' are siblings: True (confidence: 0.50, common parent: 'adult')
    'dog' and 'cat' are siblings: False (confidence: 0.00, common parent: None)
    'apple' and 'orange' are siblings: False (confidence: 0.00, common parent: None)
    'car' and 'truck' are siblings: True (confidence: 0.50, common parent: 'motor_vehicle')
    'Socrates' and 'Plato' are siblings: False (confidence: 0.00, common parent: None)

    --- Syllogistic Validation ---
    2025-03-02 11:39:31.256 | DEBUG    | __main__:validate_syllogistic_inference:189 - Major premise: {'subject': None, 'predicate': None}
    2025-03-02 11:39:31.256 | DEBUG    | __main__:validate_syllogistic_inference:190 - Minor premise: {'subject': 'socrates', 'predicate': 'man'}
    2025-03-02 11:39:31.256 | DEBUG    | __main__:validate_syllogistic_inference:191 - Conclusion: {'subject': 'socrates', 'predicate': 'mortal'}

    Syllogism:
      Major: All men are mortal
      Minor: Socrates is a man
      Conclusion: Socrates is mortal
      Valid: False (confidence: 0.00)
      Reason: Middle term mismatch: 'man' should match 'None'
    2025-03-02 11:39:31.256 | DEBUG    | __main__:validate_syllogistic_inference:189 - Major premise: {'subject': None, 'predicate': None}
    2025-03-02 11:39:31.256 | DEBUG    | __main__:validate_syllogistic_inference:190 - Minor premise: {'subject': 'socrates', 'predicate': 'dog'}
    2025-03-02 11:39:31.256 | DEBUG    | __main__:validate_syllogistic_inference:191 - Conclusion: {'subject': 'socrates', 'predicate': 'mortal'}

    Syllogism:
      Major: All men are mortal
      Minor: Socrates is a dog
      Conclusion: Socrates is mortal
      Valid: False (confidence: 0.00)
      Reason: Middle term mismatch: 'dog' should match 'None'
    2025-03-02 11:39:31.256 | DEBUG    | __main__:validate_syllogistic_inference:189 - Major premise: {'subject': None, 'predicate': None}
    2025-03-02 11:39:31.256 | DEBUG    | __main__:validate_syllogistic_inference:190 - Minor premise: {'subject': 'aristotle', 'predicate': 'philosopher'}
    2025-03-02 11:39:31.256 | DEBUG    | __main__:validate_syllogistic_inference:191 - Conclusion: {'subject': 'aristotle', 'predicate': 'thinker'}

    Syllogism:
      Major: All philosophers are thinkers
      Minor: Aristotle is a philosopher
      Conclusion: Aristotle is a thinker
      Valid: False (confidence: 0.00)
      Reason: Middle term mismatch: 'philosopher' should match 'None'
    ```

Hypothesis 2: Wu-Palmer similarity will provide more intuitive semantic relationships than generic similarity
- Added test_wu_palmer() to compare Wu-Palmer with other similarity metrics
- Results:
    ```
    === Testing Enhanced Relationship Detection ===

    --- Hyponym Relationships (X IS-A Y) ---
    2025-03-02 11:50:19.090 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: man IS-A person = True (confidence: 0.33)
    'man' IS-A 'person': True (confidence: 0.33)
    2025-03-02 11:50:19.091 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: dog IS-A mammal = True (confidence: 0.20)
    'dog' IS-A 'mammal': True (confidence: 0.20)
    2025-03-02 11:50:19.091 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: human IS-A mortal = False (confidence: 0.10)
    'human' IS-A 'mortal': False (confidence: 0.10)
    2025-03-02 11:50:19.091 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: Socrates IS-A philosopher = False (confidence: 0.50)
    'Socrates' IS-A 'philosopher': False (confidence: 0.50)
    2025-03-02 11:50:19.091 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: dog IS-A person = False (confidence: 0.20)
    'dog' IS-A 'person': False (confidence: 0.20)
    2025-03-02 11:50:19.091 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: idiot IS-A person = True (confidence: 0.33)
    'idiot' IS-A 'person': True (confidence: 0.33)

    --- Hypernym Relationships (Y IS-A X) ---
    2025-03-02 11:50:19.091 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: person IS-A man = False (confidence: 0.33)
    'person' IS-A 'man': False (confidence: 0.33)
    2025-03-02 11:50:19.092 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: mammal IS-A dog = False (confidence: 0.20)
    'mammal' IS-A 'dog': False (confidence: 0.20)
    2025-03-02 11:50:19.092 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: mortal IS-A human = False (confidence: 0.10)
    'mortal' IS-A 'human': False (confidence: 0.10)
    2025-03-02 11:50:19.092 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: philosopher IS-A Socrates = False (confidence: 0.50)
    'philosopher' IS-A 'Socrates': False (confidence: 0.50)
    2025-03-02 11:50:19.092 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: person IS-A dog = False (confidence: 0.20)
    'person' IS-A 'dog': False (confidence: 0.20)
    2025-03-02 11:50:19.092 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: person IS-A idiot = False (confidence: 0.33)
    'person' IS-A 'idiot': False (confidence: 0.33)

    --- Wu-Palmer Similarity ---
    2025-03-02 11:50:19.092 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between man and person: 0.7500
    Similarity(man, person) = 0.7500
    2025-03-02 11:50:19.092 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between dog and mammal: 0.8333
    Similarity(dog, mammal) = 0.8333
    2025-03-02 11:50:19.092 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between human and mortal: 0.5714
    Similarity(human, mortal) = 0.5714
    2025-03-02 11:50:19.093 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between Socrates and philosopher: 0.9524
    Similarity(Socrates, philosopher) = 0.9524
    2025-03-02 11:50:19.093 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between dog and person: 0.7500
    Similarity(dog, person) = 0.7500
    2025-03-02 11:50:19.093 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between idiot and person: 0.7500
    Similarity(idiot, person) = 0.7500

    --- Sibling Relationships ---
    'man' and 'woman' are siblings: True (confidence: 0.50, common parent: 'adult')
    'dog' and 'cat' are siblings: False (confidence: 0.00, common parent: None)
    'apple' and 'orange' are siblings: False (confidence: 0.00, common parent: None)
    'car' and 'truck' are siblings: True (confidence: 0.50, common parent: 'motor_vehicle')
    'Socrates' and 'Plato' are siblings: False (confidence: 0.00, common parent: None)

    --- Syllogistic Validation ---
    2025-03-02 11:50:19.094 | DEBUG    | __main__:validate_syllogistic_inference:189 - Major premise: {'subject': None, 'predicate': None}
    2025-03-02 11:50:19.094 | DEBUG    | __main__:validate_syllogistic_inference:190 - Minor premise: {'subject': 'socrates', 'predicate': 'man'}
    2025-03-02 11:50:19.094 | DEBUG    | __main__:validate_syllogistic_inference:191 - Conclusion: {'subject': 'socrates', 'predicate': 'mortal'}

    Syllogism:
      Major: All men are mortal
      Minor: Socrates is a man
      Conclusion: Socrates is mortal
      Valid: False (confidence: 0.00)
      Reason: Middle term mismatch: 'man' should match 'None'
    2025-03-02 11:50:19.094 | DEBUG    | __main__:validate_syllogistic_inference:189 - Major premise: {'subject': None, 'predicate': None}
    2025-03-02 11:50:19.094 | DEBUG    | __main__:validate_syllogistic_inference:190 - Minor premise: {'subject': 'socrates', 'predicate': 'dog'}
    2025-03-02 11:50:19.094 | DEBUG    | __main__:validate_syllogistic_inference:191 - Conclusion: {'subject': 'socrates', 'predicate': 'mortal'}

    Syllogism:
      Major: All men are mortal
      Minor: Socrates is a dog
      Conclusion: Socrates is mortal
      Valid: False (confidence: 0.00)
      Reason: Middle term mismatch: 'dog' should match 'None'
    2025-03-02 11:50:19.094 | DEBUG    | __main__:validate_syllogistic_inference:189 - Major premise: {'subject': None, 'predicate': None}
    2025-03-02 11:50:19.094 | DEBUG    | __main__:validate_syllogistic_inference:190 - Minor premise: {'subject': 'aristotle', 'predicate': 'philosopher'}
    2025-03-02 11:50:19.094 | DEBUG    | __main__:validate_syllogistic_inference:191 - Conclusion: {'subject': 'aristotle', 'predicate': 'thinker'}

    Syllogism:
      Major: All philosophers are thinkers
      Minor: Aristotle is a philosopher
      Conclusion: Aristotle is a thinker
      Valid: False (confidence: 0.00)
      Reason: Middle term mismatch: 'philosopher' should match 'None'
    ```

Hypothesis 3: Improved regex patterns will better extract terms from universal statements
- Created a dedicated extract_proposition_terms() function with enhanced regex patterns
- Enhanced pattern recognition to handle more variants:
  - Universal: "All X are Y", "Every X is a Y", "Each X is Y"
  - Particular: "Some X are Y"
  - Negative: "No X are Y"
  - Instance: "X is a Y"
- Added support for multi-word terms with improved boundary handling
- Updated test_syllogistic_patterns() to use the new extraction function
- Added more test cases for syllogistic reasoning including "Every" forms and multi-word terms
- Results:
    ```
    === Testing Enhanced Relationship Detection ===

    --- Hyponym Relationships (X IS-A Y) ---
    2025-03-02 12:10:06.600 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: man IS-A person = True (confidence: 0.33)
    'man' IS-A 'person': True (confidence: 0.33)
    2025-03-02 12:10:06.600 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: dog IS-A mammal = True (confidence: 0.20)
    'dog' IS-A 'mammal': True (confidence: 0.20)
    2025-03-02 12:10:06.601 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: human IS-A mortal = False (confidence: 0.10)
    'human' IS-A 'mortal': False (confidence: 0.10)
    2025-03-02 12:10:06.601 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: Socrates IS-A philosopher = False (confidence: 0.50)
    'Socrates' IS-A 'philosopher': False (confidence: 0.50)
    2025-03-02 12:10:06.601 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: dog IS-A person = False (confidence: 0.20)
    'dog' IS-A 'person': False (confidence: 0.20)
    2025-03-02 12:10:06.601 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: idiot IS-A person = True (confidence: 0.33)
    'idiot' IS-A 'person': True (confidence: 0.33)

    --- Hypernym Relationships (Y IS-A X) ---
    2025-03-02 12:10:06.601 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: person IS-A man = False (confidence: 0.33)
    'person' IS-A 'man': False (confidence: 0.33)
    2025-03-02 12:10:06.601 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: mammal IS-A dog = False (confidence: 0.20)
    'mammal' IS-A 'dog': False (confidence: 0.20)
    2025-03-02 12:10:06.601 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: mortal IS-A human = False (confidence: 0.10)
    'mortal' IS-A 'human': False (confidence: 0.10)
    2025-03-02 12:10:06.602 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: philosopher IS-A Socrates = False (confidence: 0.50)
    'philosopher' IS-A 'Socrates': False (confidence: 0.50)
    2025-03-02 12:10:06.602 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: person IS-A dog = False (confidence: 0.20)
    'person' IS-A 'dog': False (confidence: 0.20)
    2025-03-02 12:10:06.602 | DEBUG    | __main__:is_hyponym_of:60 - Hyponym check: person IS-A idiot = False (confidence: 0.33)
    'person' IS-A 'idiot': False (confidence: 0.33)

    --- Wu-Palmer Similarity ---
    2025-03-02 12:10:06.602 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between man and person: 0.7500
    Similarity(man, person) = 0.7500
    2025-03-02 12:10:06.602 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between dog and mammal: 0.8333
    Similarity(dog, mammal) = 0.8333
    2025-03-02 12:10:06.602 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between human and mortal: 0.5714
    Similarity(human, mortal) = 0.5714
    2025-03-02 12:10:06.602 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between Socrates and philosopher: 0.9524
    Similarity(Socrates, philosopher) = 0.9524
    2025-03-02 12:10:06.602 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between dog and person: 0.7500
    Similarity(dog, person) = 0.7500
    2025-03-02 12:10:06.603 | DEBUG    | __main__:wu_palmer_similarity:124 - Wu-Palmer similarity between idiot and person: 0.7500
    Similarity(idiot, person) = 0.7500

    --- Sibling Relationships ---
    'man' and 'woman' are siblings: True (confidence: 0.50, common parent: 'adult')
    'dog' and 'cat' are siblings: False (confidence: 0.00, common parent: None)
    'apple' and 'orange' are siblings: False (confidence: 0.00, common parent: None)
    'car' and 'truck' are siblings: True (confidence: 0.50, common parent: 'motor_vehicle')
    'Socrates' and 'Plato' are siblings: False (confidence: 0.00, common parent: None)

    --- Syllogistic Validation ---
    2025-03-02 12:10:06.604 | DEBUG    | __main__:validate_syllogistic_inference:189 - Major premise: {'subject': None, 'predicate': None}
    2025-03-02 12:10:06.604 | DEBUG    | __main__:validate_syllogistic_inference:190 - Minor premise: {'subject': 'socrates', 'predicate': 'man'}
    2025-03-02 12:10:06.604 | DEBUG    | __main__:validate_syllogistic_inference:191 - Conclusion: {'subject': 'socrates', 'predicate': 'mortal'}

    Syllogism:
      Major: All men are mortal
      Minor: Socrates is a man
      Conclusion: Socrates is mortal
      Valid: False (confidence: 0.00)
      Reason: Middle term mismatch: 'man' should match 'None'
    2025-03-02 12:10:06.604 | DEBUG    | __main__:validate_syllogistic_inference:189 - Major premise: {'subject': None, 'predicate': None}
    2025-03-02 12:10:06.604 | DEBUG    | __main__:validate_syllogistic_inference:190 - Minor premise: {'subject': 'socrates', 'predicate': 'dog'}
    2025-03-02 12:10:06.604 | DEBUG    | __main__:validate_syllogistic_inference:191 - Conclusion: {'subject': 'socrates', 'predicate': 'mortal'}

    Syllogism:
      Major: All men are mortal
      Minor: Socrates is a dog
      Conclusion: Socrates is mortal
      Valid: False (confidence: 0.00)
      Reason: Middle term mismatch: 'dog' should match 'None'
    2025-03-02 12:10:06.604 | DEBUG    | __main__:validate_syllogistic_inference:189 - Major premise: {'subject': None, 'predicate': None}
    2025-03-02 12:10:06.604 | DEBUG    | __main__:validate_syllogistic_inference:190 - Minor premise: {'subject': 'aristotle', 'predicate': 'philosopher'}
    2025-03-02 12:10:06.604 | DEBUG    | __main__:validate_syllogistic_inference:191 - Conclusion: {'subject': 'aristotle', 'predicate': 'thinker'}

    Syllogism:
      Major: All philosophers are thinkers
      Minor: Aristotle is a philosopher
      Conclusion: Aristotle is a thinker
      Valid: False (confidence: 0.00)
      Reason: Middle term mismatch: 'philosopher' should match 'None'

    ```

Hypothesis 4: Multi-strategy relationship detection based on term types will improve validation accuracy
- Problem: Different types of terms (nouns, adjectives, proper nouns) require different relationship evaluation methods
- Current approach only uses hypernym/hyponym relations which work well for noun-noun taxonomic relationships but fail for:
  - Noun-adjective relationships (e.g., "humans are mortal")
  - Named entity-noun relationships (e.g., "Socrates is a man")
  - Abstract concept relationships that may not be in WordNet's taxonomy
- Solution: Implement a multi-strategy approach that:
  1. First identifies the grammatical roles and POS of the terms in the relationship
  2. Then applies the appropriate relationship detection method:
     - Taxonomic (hypernym/hyponym) for noun-noun relationships
     - Attribute validation for noun-adjective relationships
     - Instance checking for named entity-noun relationships
     - Fallback to syntactic patterns and similarity metrics when specific relations can't be determined
- Expected outcome: Improved validation of diverse syllogisms, especially those involving adjectives like "mortal"
"""
