# ~/formalities/src/formalities/fall/core/types/language/common.py
import enum, typing as t

class WordType(enum.Enum):
    NOUN = enum.auto()
    PROPERNOUN = enum.auto()
    PRONOUN = enum.auto()
    VERB = enum.auto()
    ADJECTIVE = enum.auto()
    ADVERB = enum.auto()
    PREPOSITION = enum.auto()
    CONJUNCTION = enum.auto()
    INTERJECTION = enum.auto()
    DETERMINER = enum.auto()
    QUANTIFIER = enum.auto()

class WordFunction(enum.Enum):
    SUBJECT = enum.auto()
    PREDICATE = enum.auto()
    PREDICATENOMINATIVE = enum.auto()
    PREDICATEADJECTIVE = enum.auto()
    DIRECTOBJECT = enum.auto()
    INDIRECTOBJECT = enum.auto()
    COPULA = enum.auto()
    QUANTIFIER = enum.auto()
    ARGUMENT = enum.auto()
    COMPLEMENT = enum.auto()

class RelationshipType(enum.Enum):
    IDENTITY = enum.auto()
    INSTANCEOF = enum.auto()
    ATTRIBUTION = enum.auto()
    SUBSET = enum.auto()
    TAXONOMIC = enum.auto()
    GENERALSIMILARITY = enum.auto()

class StatementType(enum.Enum):
    UNIVERSAL = enum.auto()
    PARTICULAR = enum.auto()
    NEGATIVE = enum.auto()
    EXISTENTIAL = enum.auto()
    CONDITIONAL = enum.auto()
    INDUCTIVE = enum.auto()
    DEFINITIONAL = enum.auto()
    EVALUATIVE = enum.auto()
    FACTUAL = enum.auto()
    DECLARATIVE = enum.auto()
    INTERROGATIVE = enum.auto()
    IMPERATIVE = enum.auto()


class POS:
    TAGMAP = {
        # Nouns
        'NN': WordType.NOUN,
        'NNS': WordType.NOUN,
        'NNP': WordType.PROPERNOUN,
        'NNPS': WordType.PROPERNOUN,
        # Verbs
        'VB': WordType.VERB,
        'VBD': WordType.VERB,
        'VBG': WordType.VERB,
        'VBN': WordType.VERB,
        'VBP': WordType.VERB,
        'VBZ': WordType.VERB,
        # Adjectives
        'JJ': WordType.ADJECTIVE,
        'JJR': WordType.ADJECTIVE,
        'JJS': WordType.ADJECTIVE,
        # Adverbs
        'RB': WordType.ADVERB,
        'RBR': WordType.ADVERB,
        'RBS': WordType.ADVERB,
        # Prepositions
        'IN': WordType.PREPOSITION,
        # Determiners
        'DT': WordType.DETERMINER,
        # Pronouns
        'PRP': WordType.PRONOUN,
        'PRP$': WordType.PRONOUN,
        'WP': WordType.PRONOUN,
        'WP$': WordType.PRONOUN,
        # Conjunctions
        'CC': WordType.CONJUNCTION,
        # Interjections
        'UH': WordType.INTERJECTION
    }
    LEMMAMAP = {
        WordType.NOUN: 'n',
        WordType.PROPERNOUN: 'n',
        WordType.VERB: 'v',
        WordType.ADJECTIVE: 'a',
        WordType.ADVERB: 'r'
    }

class KNOWN:
    QUANTIFIERS = {
        'all', 'every', 'each', 'any', 'some', 'no', 'many', 'few', 'most', 'several'
    }
    COPULI = {
        'is', 'am', 'are', 'was', 'were', 'be', 'being', 'been'
    }
    ARTICLES = {
        'a', 'an', 'the'
    }


class PATTERNS:
    STATEMENTTYPES = {
        StatementType.UNIVERSAL: {
            'startswith': ['all', 'every', 'each'],
        },
        StatementType.PARTICULAR: {
            'startswith': ['some', 'many', 'few', 'most'],
        },
        StatementType.NEGATIVE: {
            'startswith': ['no', 'not'],
            'contains': ['not', "n't", 'never'],
        },
        StatementType.INTERROGATIVE: {
            'startswith': ['what', 'when', 'where', 'who', 'whom', 'whose', 'which', 'why', 'how'],
            'endswith': ['?'],
        },
        StatementType.IMPERATIVE: {
            'startswithverb': True,
            'endswith': ['!', '.'],
        },
        # Default to DECLARATIVE if no other patterns match
    }

    RELATIONSHIP = {
        # Subject is proper noun, predicate is noun with article
        # Example: "Socrates is a man"
        RelationshipType.INSTANCEOF: {
            'types': {
                'subject': WordType.PROPERNOUN,
                'predicate': WordType.NOUN
            },
            'has': {
                'copula': True,
                'article': True
            },
        },
        # Subject and predicate are both nouns, often with article
        # Example: "A dog is an animal"
        RelationshipType.IDENTITY: {
            'types': {
                'subject': WordType.NOUN,
                'predicate': WordType.NOUN
            },
            'has': {
                'copula': True
            },
        },
        # Predicate is an adjective
        # Example: "Socrates is mortal"
        RelationshipType.ATTRIBUTION: {
            'types': {
                'predicate': WordType.ADJECTIVE
            },
            'has': {
                'copula': True
            },
        },
        # Universal statement with noun predicate
        # Example: "All men are humans"
        RelationshipType.SUBSET: {
            'statementtype': StatementType.UNIVERSAL,
            'types': {
                'predicate': WordType.NOUN
            }
        },
        # Universal statement with adjective predicate
        # Example: "All men are mortal"
        RelationshipType.TAXONOMIC: {
            'types': {
                'subject': WordType.NOUN,
                'predicate': WordType.NOUN
            }
        }
    }

    WORDFUNCTIONS = {
        # For declarative statements like "Socrates is a man"
        'declarative': {
            'positions': {
                0: WordFunction.SUBJECT,            # First word is subject
                1: 'CopulaCheck',                  # Second word should be a copula
                2: None,                           # Third word might be an article (skip it)
                3: WordFunction.PREDICATENOMINATIVE # Fourth word should be predicate nominative
            },
            # Special case for no article: "Socrates is mortal"
            'alternate': {
                0: WordFunction.SUBJECT,
                1: 'CopulaCheck',
                2: WordFunction.PREDICATEADJECTIVE
            }
        },
        # For universal statements like "All men are mortal"
        'universal': {
            'positions': {
                0: WordFunction.QUANTIFIER,         # First word is quantifier
                1: WordFunction.SUBJECT,            # Second word is subject
                2: 'CopulaCheck',                  # Third word should be a copula
                3: WordFunction.PREDICATENOMINATIVE # Fourth word should be predicate
            }
        }
    }

class CheckFunctions:
    @staticmethod
    def CopulaCheck(word: str) -> t.Optional[WordFunction]:
        return WordFunction.COPULA if word.lower() in KNOWN.COPULI else None

    @staticmethod
    def ArticleCheck(word: str) -> (t.Optional[WordFunction] | bool):
        return None if word.lower() in KNOWN.ARTICLES else False

    @staticmethod
    def PredicateCheck(word: str, typeof: WordType) -> t.Optional[WordFunction]:
        if typeof == WordType.ADJECTIVE:
            return WordFunction.PREDICATEADJECTIVE
        elif typeof in [WordType.NOUN, WordType.PROPERNOUN]:
            return WordFunction.PREDICATENOMINATIVE
        else:
            return WordFunction.PREDICATE




"""
CHANGES:
    1. removed `KNOWN.PLURALS`
        reason: violates design principle
    2. restructured `FUNCTIONS` as CheckFunctions , with methods being static
        > also removed `is_hyponym_of` -- did not see a reference to it, felt excessive.


"""
