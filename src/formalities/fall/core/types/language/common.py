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
    NUMBER = enum.auto()
    UNIT = enum.auto()
    FRACTION = enum.auto()
    PERCENTAGE = enum.auto()
    ORDINAL = enum.auto()
    RATIO = enum.auto()

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
    OPERAND = enum.auto()
    OPERATOR = enum.auto()
    COUNTABLE = enum.auto()
    CONTAINER = enum.auto()
    RESULT = enum.auto()

class RelationshipType(enum.Enum):
    IDENTITY = enum.auto()
    INSTANCEOF = enum.auto()
    ATTRIBUTION = enum.auto()
    SUBSET = enum.auto()
    TAXONOMIC = enum.auto()
    GENERALSIMILARITY = enum.auto()
    COUNTING = enum.auto()
    EQUALITY = enum.auto()
    COMPARISON = enum.auto()
    ARITHMETIC = enum.auto()
    MEASUREMENT = enum.auto()
    PROPORTION = enum.auto()
    DISTRIBUTION = enum.auto()
    RATE = enum.auto()
    PROBABILITY = enum.auto()
    PROGRESSION = enum.auto()

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
    NUMERICAL = enum.auto()


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
    NUMBERWORDS = {'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten'}
    ARITHMETICOPERATORS = {
        'plus', 'add', 'minus', 'subtract', 'times', 'multiply', 'divide',
        'divided by', 'multiplied by', 'added to', 'subtracted from'
    }
    COMPARANS = {
        'greater than', 'less than', 'equal to', 'more than', 'fewer than',
        'at least', 'at most', 'exactly', 'approximately'
    }
    UNITS = {
        # Time
        'second', 'minute', 'hour', 'day', 'week', 'month', 'year',
        # Length
        'meter', 'kilometer', 'inch', 'foot', 'yard', 'mile',
        # Weight
        'gram', 'kilogram', 'pound', 'ounce', 'ton',
        # Volume
        'liter', 'gallon', 'quart', 'pint', 'cup',
        # Other
        'degree', 'percent', 'dollar', 'euro'
    }
    class COUNTING:
        NOUNS = {
            'number', 'count', 'total', 'sum', 'amount', 'quantity'
        }
        VERBS = {
            'count', 'tally', 'enumerate', 'total'
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
        StatementType.NUMERICAL: {
            'startswith': ['how many', 'count', 'calculate', 'compute'],
            'contains': [
                # Counting patterns
                'are there', 'there are', 'has', 'have', 'contain', 'consists of',
                # Arithmetic patterns
                'plus', 'minus', 'times', 'divided by', 'equals', 'is equal to',
                'add', 'subtract', 'multiply', 'divide',
                # Number presence patterns
                'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
                '1', '2', '3', '4', '5', '6', '7', '8', '9', '0'
            ],
            # Check for digit presence
            'hasdigit': True
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
        },
        # Counting statement
        # Example: "There are 2 r's in strawberry"
        RelationshipType.COUNTING: {
            'statementtype': StatementType.NUMERICAL,
            'contains': ['in', 'there are', 'has', 'have', 'how many'],
            'has': {
                'number': True
            }
        },
        # Arithmetic relationship
        # Example: "2 plus 2 equals 4"
        RelationshipType.ARITHMETIC: {
            'statementtype': StatementType.NUMERICAL,
            'contains': KNOWN.ARITHMETICOPERATORS,
            'has': {
                'number': True
            }
        },
        # Comparison relationship
        # Example: "5 is greater than 3"
        RelationshipType.COMPARISON: {
            'statementtype': StatementType.NUMERICAL,
            'contains': KNOWN.COMPARANS,
            'has': {
                'number': True
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
        },
        # For counting statements like "There are 2 r's in strawberry"
        'counting': {
            'positions': {
                0: None,                           # "There" (skip)
                1: 'CopulaCheck',                  # "are" (copula)
                2: WordFunction.RESULT,            # "2" (count result)
                3: WordFunction.COUNTABLE,         # "r's" (what's being counted)
                4: None,                           # "in" (skip preposition)
                5: WordFunction.CONTAINER          # "strawberry" (where counting happens)
            },
            # Alternate form: "Strawberry has 2 r's"
            'alternate': {
                0: WordFunction.CONTAINER,         # "Strawberry" (container)
                1: 'CopulaCheck',                  # "has" (treated as copula)
                2: WordFunction.RESULT,            # "2" (count result)
                3: WordFunction.COUNTABLE          # "r's" (what's being counted)
            }
        },
        # For arithmetic statements like "2 plus 2 equals 4"
        'arithmetic': {
            'positions': {
                0: WordFunction.OPERAND,           # First number
                1: WordFunction.OPERATOR,          # Operator (plus)
                2: WordFunction.OPERAND,           # Second number
                3: 'CopulaCheck',                  # "equals"
                4: WordFunction.RESULT             # Result number
            }
        }
    }
    NUMERICALCHECKS = {
        'hasdigit': (lambda text: any(c.isdigit() for c in text)),
        'iscounting': (lambda text: any(term in text.lower() for term in KNOWN.COUNTING.VERBS) or any(term in text.lower() for term in KNOWN.COUNTING.NOUNS)),
        'isarithmetic': (lambda text: any(op in text.lower() for op in KNOWN.ARITHMETICOPERATORS)),
        'hascomparison': (lambda text: any(term in text.lower() for term in KNOWN.COMPARANS))
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

    @staticmethod
    def NumberCheck(word: str) -> bool:
        """check if a word is a number (digit or word form)"""
        return (word.isdigit() or word.lower() in KNOWN.NUMBERWORDS)

    @staticmethod
    def OperatorCheck(word:str) -> t.Optional[WordFunction]:
        if word.lower() in KNOWN.ARITHMETICOPERATORS:
            return WordFunction.OPERATOR
        return None
