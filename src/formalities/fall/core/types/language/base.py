# ~/formalities/src/formalities/fall/core/types/language/base.py
from __future__ import annotations
import re, enum, typing as t
from dataclasses import dataclass, field, fields, asdict
from formalities.fall.core.types.language.common import (
    WordType, WordFunction, RelationshipType, StatementType,
    POS, KNOWN, PATTERNS, CheckFunctions
)
import nltk
from nltk import pos_tag
from nltk.stem import WordNetLemmatizer
from loguru import logger as log


# Ensure NLTK resources are available
# maybe move this to the __init__.py


try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('averaged_perceptron_tagger')
    nltk.download('wordnet')

@dataclass
class Word:
    content: str
    _type: t.Optional[WordType] = None
    _function: t.Optional[WordFunction] = None
    _lemma: t.Optional[str] = None # base form (e.g. "men" -> "man")

    def _determinelemma(self) -> str:
        """Get base form of the word using NLTK lemmatizer"""
        lemmatizer = WordNetLemmatizer()

        if self._type in POS.LEMMAMAP:
            code = POS.LEMMAMAP[self._type]
            return lemmatizer.lemmatize(self.content.lower(), code)
        return lemmatizer.lemmatize(self.content.lower())

    def _determinetype(self) -> WordType:
        if self.content.lower() in KNOWN.QUANTIFIERS:
            return WordType.QUANTIFIER
        if CheckFunctions.NumberCheck(self.content):
            return WordType.NUMBER
        if self.content.lower() in KNOWN.UNITS:
            return WordType.UNIT
        if self.content.lower() in KNOWN.ARITHMETICOPERATORS:
            return WordType.VERB # treat operators as verbs initially

        tagged = pos_tag([self.content])
        tag = tagged[0][1]

        if tag in POS.TAGMAP:
            return POS.TAGMAP[tag]

        # default to NOUN for now
        return WordType.NOUN

    def _determinefunction(self) -> WordFunction:
        pass

    def __post_init__(self):
        if self._type is None:
            self._type = self._determinetype()
        if self._lemma is None:
            self._lemma = self._determinelemma()

    @property
    def type(self) -> WordType:
        if self._type is None:
            self._type = self._determinetype()
        return self._type

    @property
    def lemma(self) -> str:
        if self._lemma is None:
            self._lemma = self._determinelemma()
        return self._lemma

    @property
    def function(self) -> t.Optional[WordFunction]:
        """Get the word's grammatical function."""
        return self._function

    @function.setter
    def function(self, func: WordFunction):
        self._function = func

@dataclass
class Statement:
    content: str
    _type: t.Optional[StatementType] = None
    _words: t.Optional[t.List[Word]] = field(default_factory=list)
    _relationships: t.Optional[t.List[RelationshipType]] = field(default_factory=list)
    _numericalstructure: t.Optional[dict] = None

    def _parsewords(self):
        self._words = [Word(token) for token in self.content.strip().split()]

    def _determinetype(self) -> StatementType:
        content = self.content.lower()
        if (
            PATTERNS.NUMERICALCHECKS['hasdigit'](content)
            or
            PATTERNS.NUMERICALCHECKS['iscounting'](content)
            or
            PATTERNS.NUMERICALCHECKS['isarithmetic'](content)
            or
            PATTERNS.NUMERICALCHECKS['hascomparison'](content)
        ):
            return StatementType.NUMERICAL
        for typeof, patterns in PATTERNS.STATEMENTTYPES.items():
            if 'startswith' in patterns:
                for prefix in patterns['startswith']:
                    if content.startswith(prefix):
                        return typeof
            if 'contains' in patterns:
                for term in patterns['contains']:
                    if term in content:
                        return typeof
            if 'endswith' in patterns:
                for suffix in patterns['endswith']:
                    if content.endswith(suffix):
                        return typeof
            if 'startswithverb' in patterns and patterns['startswithverb']:
                if self._words and self._words[0].type == WordType.VERB:
                    return typeof
        # default to declarative for now
        return StatementType.DECLARATIVE

    def _assignnumericalfunctions(self) -> None:
        # First pass: identify multi-word operators like "divided by"
        for i in range(len(self._words)-1):
            if (self._words[i].content.lower() == 'divided' and
                i+1 < len(self._words) and
                self._words[i+1].content.lower() == 'by'):
                # Mark only the first word as the operator and remember it's a multi-word operator
                self._words[i].function = WordFunction.OPERATOR
                self._words[i].content = "divided by"  # Store the full operator phrase

                # Remove the function from the second word to avoid confusion
                self._words[i+1].function = None

                # Mark the number after "by" as an operand if present
                if i+2 < len(self._words) and self._words[i+2].type == WordType.NUMBER:
                    self._words[i+2].function = WordFunction.OPERAND
        for i, word in enumerate(self._words):
            if word.type == WordType.NUMBER:
                if (i>0) and (i<len(self._words)-1):
                    # Number in the middle - likely operand or result
                    prevword = self._words[i-1]
                    nextword = self._words[i+1] if i+1 < len(self._words) else None
                    if nextword and (nextword.content.lower() in KNOWN.ARITHMETICOPERATORS):
                        word.function = WordFunction.OPERAND
                    elif prevword and (prevword.content.lower() in KNOWN.ARITHMETICOPERATORS):
                        word.function = WordFunction.OPERAND
                    elif prevword and (prevword.content.lower() in ['equals', 'is']):
                        word.function = WordFunction.RESULT
                elif i == 0:
                    # Number at start - likely first operand
                    word.function = WordFunction.OPERAND
                elif i == (len(self._words) - 1):
                    # Number at end - likely result
                    word.function = WordFunction.RESULT

            elif word.content.lower() in KNOWN.ARITHMETICOPERATORS:
                word.function = WordFunction.OPERATOR
        for i in range(len(self._words)):
            if (i>0) and (i<len(self._words)-1):
                if self._words[i].content.lower() == 'in':
                    if (i-1>=0) and ("'" in self._words[i].content):
                        self._words[i-1].function = WordFunction.COUNTABLE
                    if (i+1 < len(self._words)):
                        self._words[i+1].function = WordFunction.CONTAINER

    def _assignwordfunctions(self) -> None:
        log.debug(f"Assigning functions for: '{self.content}'")
        patternkey = 'declarative'
        if self._type == StatementType.UNIVERSAL:
            patternkey = 'universal'

        log.debug(f"  Using pattern: {patternkey}")
        pattern = PATTERNS.WORDFUNCTIONS.get(patternkey, {})
        positions = pattern.get('positions', {})
        usealt = False

        # Check if we need the alternate pattern
        if (len(self._words) >= 3) and pattern.get('alternate'):
            # If third word is not an article, use alternate pattern
            if self._words[2].content.lower() not in KNOWN.ARTICLES:
                log.debug(f"  Using alternate pattern (no article detected)")
                positions = pattern.get('alternate', {})
                usealt = True

        log.debug(f"  Positions to process: {positions}")
        for pos, funcorcheck in positions.items():
            if (pos < len(self._words)):
                log.debug(f"  Position {pos}: '{self._words[pos].content}', function={funcorcheck}")
                if isinstance(funcorcheck, WordFunction):
                    self._words[pos].function = funcorcheck
                    log.debug(f"    Assigned: {funcorcheck}")
                elif funcorcheck == 'CopulaCheck':
                    # special case for copulas
                    if self._words[pos].content.lower() in KNOWN.COPULI:
                        self._words[pos].function = WordFunction.COPULA
                        log.debug(f"    Assigned: COPULA")
                    else:
                        log.debug(f"    Not a copula")
                elif funcorcheck is None:
                    # skip this position (for now) (likely an article)
                    log.debug(f"    Skipping (likely article)")

        if self._type == StatementType.NUMERICAL:
            self._assignnumericalfunctions()

        if (not usealt) and (len(self._words) > 3):
            if (len(self._words) > 2 and
                self._words[1].function == WordFunction.COPULA and
                self._words[2].content.lower() in KNOWN.ARTICLES):

                log.debug(f"  Detected 'X is a Y' pattern")
                # The word after the article should be a predicate nominative
                if len(self._words) > 3:
                    if self._words[3].type == WordType.ADJECTIVE:
                        self._words[3].function = WordFunction.PREDICATEADJECTIVE
                        log.debug(f"    Assigned position 3 '{self._words[3].content}': PREDICATEADJECTIVE")
                    else:
                        self._words[3].function = WordFunction.PREDICATENOMINATIVE
                        log.debug(f"    Assigned position 3 '{self._words[3].content}': PREDICATENOMINATIVE")

        # Log final word function assignments
        log.debug("  Final function assignments:")
        for word in self._words:
            log.debug(f"    '{word.content}': {word.function}")

    def _determinerelationships(self) -> None:
        self._relationships = []

        for reltype, pattern in PATTERNS.RELATIONSHIP.items():
            matched = True
            if 'statementtype' in pattern and self._type != pattern.get('statementtype'):
                continue

            if 'types' in pattern:
                typeconstraints = pattern.get('types', {})

                if 'subject' in typeconstraints:
                    if not (subjects := self.subjects) or (subjects[0].type != typeconstraints['subject']):
                        matched = False

                if 'predicate' in typeconstraints:
                    predicates = self.predicates
                    predicates.extend(
                        self._getwordsbyfunction(
                            WordFunction.PREDICATENOMINATIVE
                        )
                    )
                    predicates.extend(
                        self._getwordsbyfunction(
                            WordFunction.PREDICATEADJECTIVE
                        )
                    )
                    if (not predicates) or (predicates[0].type != typeconstraints['predicate']):
                        matched = False

            if 'has' in pattern:
                hasconstraints = pattern.get('has', {})
                if ('copula' in hasconstraints) and (hasconstraints.get('copula', False)):
                    if not self.copuli:
                        matched = False
                if ('article' in hasconstraints) and (hasconstraints.get('article', False)):
                    articlespresent = any(w.content.lower() in KNOWN.ARTICLES for w in self._words)
                    if not articlespresent:
                        matched = False
                if ('number' in hasconstraints) and (hasconstraints.get('number', False)):
                    numberpresent = any(w.type == WordType.NUMBER for w in self._words)
                    if not numberpresent:
                        matched = False

            if 'contains' in pattern:
                containterms = pattern.get('contains', [])
                containmatched = False
                for term in containterms:
                    if term in self.content.lower():
                        containmatched = True
                        break
                if not containmatched:
                    matched = False

            if matched:
                self._relationships.append(reltype)

        # default to general similarity for now
        if not self._relationships:
            self._relationships.append(RelationshipType.GENERALSIMILARITY)

    def _extractnumericalstructure(self) -> dict:
        """
        Extract structured information from numerical statements.
        This provides a general framework for analyzing and validating numerical claims.
        """
        if self._numericalstructure is not None:
            return self._numericalstructure
        structure = {
            'operationtype': None,
            'numbers': [],
            'countable': None,
            'container': None,
            'pattern': None,
            'result': None,
            'components': {}
        }
        if RelationshipType.COUNTING in self._relationships:
            structure['operationtype'] = 'counting'
        elif RelationshipType.ARITHMETIC in self._relationships:
            structure['operationtype'] = 'arithmetic'
        elif RelationshipType.COMPARISON in self._relationships:
            structure['operationtype'] = 'comparison'
        elif RelationshipType.MEASUREMENT in self._relationships:
            structure['operationtype'] = 'measurement'

        for word in self._words:
            if word.type == WordType.NUMBER:
                try:
                    if word.content.lower() in KNOWN.NUMBERWORDS:
                       numbermapping = {name: idx for idx, name in enumerate(list(KNOWN.NUMBERWORDS))}
                       value = numbermapping.get(word.content.lower(), 0)
                    else:
                       value = int(word.content)
                    structure['numbers'].append({
                        'word': word.content,
                        'value': value,
                        'function': word.function.name if word.function else None
                    })
                    if word.function == WordFunction.RESULT:
                        structure['result'] = value
                except (ValueError, TypeError):
                    # handle non-integer numbers
                    pass
        if structure['operationtype'] == 'counting':
            countables = self._getwordsbyfunction(WordFunction.COUNTABLE)
            containers = self._getwordsbyfunction(WordFunction.CONTAINER)
            if countables:
                countabletext = countables[0].content
                if (pattern:=re.search(r"([a-z])'?s?", countabletext.lower())):
                    structure['countable'] = pattern.group(1)
                else:
                    structure['countable'] = countabletext
            if containers:
                structure['container'] = containers[0].content
            if (structure['countable'] and structure['container']):
                structure['pattern'] = structure['countable']
                structure['actualcount'] = structure['container'].lower().count(structure['countable'].lower())
                if (resultnums:=[n for n in structure['numbers'] if n.get('function') == 'RESULT']):
                    structure['claimedcount'] = resultnums[0]['value']
                    structure['isvalid'] = structure['claimedcount'] == structure['actualcount']
        elif structure['operationtype'] == 'arithmetic':
            operands = []
            operator = None
            for word in self._words:
                if word.function == WordFunction.OPERAND:
                    try:
                        value = int(word.content) if word.content.isdigit() else KNOWN.NUMBERWORDS.index(word.content.lower())
                        operands.append(value)
                    except (ValueError, IndexError):
                        pass
                elif word.function == WordFunction.OPERATOR:
                    operator = word.content.lower()

            structure['components']['operands'] = operands
            structure['components']['operator'] = operator

            if len(operands) >= 2 and operator:
                if operator in ['plus', 'add', 'added to']:
                    expected = operands[0] + operands[1]
                elif operator in ['minus', 'subtract', 'subtracted from']:
                    expected = operands[0] - operands[1]
                elif operator in ['times', 'multiply', 'multiplied by']:
                    expected = operands[0] * operands[1]
                elif operator in ['divide', 'divided by'] and operands[1] != 0:
                    expected = operands[0] / operands[1]
                else:
                    expected = None

                structure['components']['expectedresult'] = expected

                if structure['result'] is not None and expected is not None:
                    structure['isvalid'] = (structure['result'] == expected)

        self._numericalstructure = structure
        return structure

    def __post_init__(self):
        if not self._words:
            self._parsewords()

        if self._type is None:
            self._type = self._determinetype()

        self._assignwordfunctions()

        if not self._relationships:
            self._determinerelationships()

    def _getwordsbytype(self, type: WordType) -> t.List[Word]:
        if not self._words:
            return []
        return [word for word in self._words if word.type == type]

    def _getwordsbyfunction(self, function: WordFunction) -> t.List[Word]:
        if not self._words:
            return []
        return [word for word in self._words if word.function == function]

    @property
    def type(self) -> StatementType:
        if self._type is None:
            self._type = self._determinetype()
        return self._type

    @property
    def nouns(self) -> t.List[Word]:
        return self._getwordsbytype(WordType.NOUN)

    @property
    def pronouns(self) -> t.List[Word]:
        return self._getwordsbytype(WordType.PRONOUN)

    @property
    def verbs(self) -> t.List[Word]:
        return self._getwordsbytype(WordType.VERB)

    @property
    def adjectives(self) -> t.List[Word]:
        return self._getwordsbytype(WordType.ADJECTIVE)

    @property
    def adverbs(self) -> t.List[Word]:
        return self._getwordsbytype(WordType.ADVERB)

    @property
    def prepositions(self) -> t.List[Word]:
        return self._getwordsbytype(WordType.PREPOSITION)

    @property
    def conjunctions(self) -> t.List[Word]:
        return self._getwordsbytype(WordType.CONJUNCTION)

    @property
    def interjections(self) -> t.List[Word]:
        return self._getwordsbytype(WordType.INTERJECTION)

    @property
    def subjects(self) -> t.List[Word]:
        return self._getwordsbyfunction(WordFunction.SUBJECT)

    @property
    def predicates(self) -> t.List[Word]:
        return self._getwordsbyfunction(WordFunction.PREDICATE)

    @property
    def predicatenominatives(self) -> t.List[Word]:
        return self._getwordsbyfunction(WordFunction.PREDICATENOMINATIVE)

    @property
    def predicateadjectives(self) -> t.List[Word]:
        return self._getwordsbyfunction(WordFunction.PREDICATEADJECTIVE)

    @property
    def directobjects(self) -> t.List[Word]:
        return self._getwordsbyfunction(WordFunction.DIRECTOBJECT)

    @property
    def indirectobjects(self) -> t.List[Word]:
        return self._getwordsbyfunction(WordFunction.INDIRECTOBJECT)

    @property
    def copuli(self) -> t.List[Word]:
        return self._getwordsbyfunction(WordFunction.COPULA)

    @property
    def quantifiers(self) -> t.List[Word]:
        return self._getwordsbyfunction(WordFunction.QUANTIFIER)

    @property
    def arguments(self) -> t.List[Word]:
        return self._getwordsbyfunction(WordFunction.ARGUMENT)

    @property
    def complements(self) -> t.List[Word]:
        return self._getwordsbyfunction(WordFunction.COMPLEMENT)

    @property
    def primaryrelationship(self) -> RelationshipType:
        if not self._relationships:
            self._determinerelationships()
        return self._relationships[0] if self._relationships else RelationshipType.GENERALSIMILARITY

    @property
    def numericalstructure(self) -> t.Optional[dict]:
        if self._type != StatementType.NUMERICAL:
            return None
        return self._extractnumericalstructure()

    def validatenumerical(self) -> t.Tuple[bool, str]:
        if self._type != StatementType.NUMERICAL:
            return (False, "Not a numerical statement")

        structure = self._extractnumericalstructure()

        if 'isvalid' not in structure:
            return (False, "Cannot validate - insufficient information")

        if structure['isvalid']:
            if structure['operationtype'] == 'counting':
                return (True, f"Correct: There are {structure['actualcount']} {structure['countables']}'s in '{structure['container']}'")
            elif structure['operationtype'] == 'arithmetic':
                return (True, f"Correct: The result is {structure['result']}")
            return (True, "The numerical statement is valid")
        else:
            if structure['operationtype'] == 'counting':
                return (False, f"Incorrect: There are {structure.get('actualcount', '?')} {structure['countable']}'s in '{structure['container']}', not {structure.get('claimedcount', '?')}")
            elif structure['operationtype'] == 'arithmetic':
                return (False, f"Incorrect: The result should be {structure['components'].get('expectedresult', '?')}, not {structure['result']}")
            return (False, "The numerical statement is invalid")
