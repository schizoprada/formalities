# ~/formalities/src/formalities/fall/core/types/language/base.py
from __future__ import annotations
import enum, typing as t
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

    def _parsewords(self):
        self._words = [Word(token) for token in self.content.strip().split()]

    def _determinetype(self) -> StatementType:
        content = self.content.lower()
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
            if 'statementtype' in pattern and self._type != pattern['statementtype']:
                continue
            if 'type' in pattern:
                typeconstraints = pattern['types']

                if 'subject' in typeconstraints:
                    if not (subjects:=self.subjects) or (subjects[0].type != typeconstraints['subject']):
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
                if ('copula' in (hasconstraints:=pattern['has'])) and (hasconstraints['copula']):
                    if not self.copuli:
                        matched = False
                if ('article' in hasconstraints) and (hasconstraints['article']):
                    articlespresent = any(w.content.lower() in KNOWN.ARTICLES for w in self._words)
                    if not articlespresent:
                        matched = False

            if matched:
                self._relationships.append(reltype)

        # default to general similarity for now
        if not self._relationships:
            self._relationships.append(RelationshipType.GENERALSIMILARITY)

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
