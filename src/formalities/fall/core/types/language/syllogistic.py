# ~/formalities/src/formalities/fall/core/types/language/syllogistic.py
from __future__ import annotations
import enum, typing as t
from dataclasses import dataclass, field, fields, asdict
from nltk.corpus import wordnet as wn
from formalities.fall.core.types.language.common import (
    WordType, WordFunction, RelationshipType, StatementType,
    POS, KNOWN, PATTERNS, CheckFunctions
)
from formalities.fall.core.types.language.base import (
    Word, Statement
)
from loguru import logger as log


class ValidationResultStatus(enum.Enum):
    VALID = enum.auto()
    INVALID = enum.auto()
    UNDETERMINED = enum.auto()


class ValidationResult:
    def __init__(self, status: ValidationResultStatus = ValidationResultStatus.UNDETERMINED, message: str = ""):
        self.status = status
        self.message = message

    @property
    def isvalid(self) -> bool:
        return self.status == ValidationResultStatus.VALID

    def __bool__(self) -> bool:
        return self.isvalid

    def __str__(self) -> str:
        return f"{self.status.value}: {self.message}"


@dataclass
class SyllogisticForm:
    majorterm: str
    minorterm: str
    middleterm: str

    def __str__(self) -> str:
        return f"Major: {self.majorterm}, Minor: {self.minorterm}, Middle: {self.middleterm}"


@dataclass
class Syllogism:
    majorpremise: Statement
    minorpremise: Statement
    conclusion: Statement
    _form: t.Optional[SyllogisticForm] = None
    _structuralvalidation: t.Optional[ValidationResult] = None
    _semanticvalidation: t.Optional[ValidationResult] = None

    def _extractform(self) -> None:
        """Extract the major, minor, and middle terms from the syllogism."""
        try:
            # Print detailed diagnostic information
            print("\nExtracting syllogistic form:")

            # Extract major premise terms
            major_subjects = [w for w in self.majorpremise.subjects if w.type != WordType.QUANTIFIER]
            print(f"  Major premise subjects: {[w.content for w in major_subjects]}")
            print(f"  Major premise subjects lemmas: {[w.lemma for w in major_subjects]}")

            major_predicates = []
            major_predicates.extend(self.majorpremise.predicateadjectives)
            major_predicates.extend(self.majorpremise.predicatenominatives)
            major_predicates.extend(self.majorpremise.predicates)
            print(f"  Major premise predicates: {[w.content for w in major_predicates]}")
            print(f"  Major premise predicates lemmas: {[w.lemma for w in major_predicates]}")

            # Extract minor premise terms
            minor_predicates = []
            minor_predicates.extend(self.minorpremise.predicateadjectives)
            minor_predicates.extend(self.minorpremise.predicatenominatives)
            minor_predicates.extend(self.minorpremise.predicates)
            print(f"  Minor premise predicates: {[w.content for w in minor_predicates]}")
            print(f"  Minor premise predicates lemmas: {[w.lemma for w in minor_predicates]}")

            minor_subject = self.minorpremise.subjects[0] if self.minorpremise.subjects else None
            print(f"  Minor premise subject: {minor_subject.content if minor_subject else None}")
            print(f"  Minor premise subject lemma: {minor_subject.lemma if minor_subject else None}")

            # Extract conclusion terms
            conclusion_predicates = []
            conclusion_predicates.extend(self.conclusion.predicateadjectives)
            conclusion_predicates.extend(self.conclusion.predicatenominatives)
            conclusion_predicates.extend(self.conclusion.predicates)
            print(f"  Conclusion predicates: {[w.content for w in conclusion_predicates]}")
            print(f"  Conclusion predicates lemmas: {[w.lemma for w in conclusion_predicates]}")

            conclusion_subject = self.conclusion.subjects[0] if self.conclusion.subjects else None
            print(f"  Conclusion subject: {conclusion_subject.content if conclusion_subject else None}")
            print(f"  Conclusion subject lemma: {conclusion_subject.lemma if conclusion_subject else None}")

            # Use SpaCy for better lemmatization
            import spacy
            try:
                nlp = spacy.load("en_core_web_sm")

                # Apply SpaCy lemmatization to subjects/predicates
                def get_spacy_lemma(word):
                    doc = nlp(word.content)
                    # Return the first token's lemma (there should only be one for single words)
                    return doc[0].lemma_ if len(doc) > 0 else word.lemma

                # Get improved lemmas
                major_subj_lemmas = [get_spacy_lemma(w) for w in major_subjects]
                minor_pred_lemmas = [get_spacy_lemma(w) for w in minor_predicates]

                print(f"  SpaCy major subject lemmas: {major_subj_lemmas}")
                print(f"  SpaCy minor predicate lemmas: {minor_pred_lemmas}")

                # Determine major term (predicate of major premise)
                major_term = major_predicates[0].lemma if major_predicates else None

                # Determine minor term (subject of conclusion)
                minor_term = conclusion_subject.lemma if conclusion_subject else None

                # Find middle term - using SpaCy lemmas for better matching
                middle_term = None

                # Compare lemmas to find the middle term
                if major_subjects and minor_predicates:
                    for i, subj in enumerate(major_subjects):
                        for j, pred in enumerate(minor_predicates):
                            spacy_subj_lemma = major_subj_lemmas[i]
                            spacy_pred_lemma = minor_pred_lemmas[j]

                            print(f"  Comparing with SpaCy lemmas: {spacy_subj_lemma} with {spacy_pred_lemma}")

                            if spacy_subj_lemma == spacy_pred_lemma:
                                middle_term = spacy_subj_lemma
                                print(f"  Match found! Middle term = {middle_term}")
                                break

                        if middle_term:
                            break
            except:
                print("  SpaCy not available or error occurred, using original lemmas")
                # Fallback to original lemmas

                # Determine major term (predicate of major premise)
                major_term = major_predicates[0].lemma if major_predicates else None

                # Determine minor term (subject of conclusion)
                minor_term = conclusion_subject.lemma if conclusion_subject else None

                # Find middle term - using original lemmas
                middle_term = None

                if major_subjects and minor_predicates:
                    for subj in major_subjects:
                        for pred in minor_predicates:
                            print(f"  Comparing original lemmas: {subj.lemma} with {pred.lemma}")
                            if subj.lemma == pred.lemma:
                                middle_term = subj.lemma
                                print(f"  Match found! Middle term = {middle_term}")
                                break

                        if middle_term:
                            break

            self._form = SyllogisticForm(major_term, minor_term, middle_term)
            print(f"  Extracted form: Major={major_term}, Minor={minor_term}, Middle={middle_term}")

        except Exception as e:
            print(f"Error extracting syllogistic form: {str(e)}")
            import traceback
            print(traceback.format_exc())
            self._form = SyllogisticForm(None, None, None)

    def _validatestructure(self) -> None:

        missingterms = []
        if not self._form.majorterm:
            missingterms.append("major term")
        if not self._form.minorterm:
            missingterms.append("minor term")
        if not self._form.middleterm:
            missingterms.append("middle term")
        if missingterms:
            self._structuralvalidation = ValidationResult(
                ValidationResultStatus.INVALID,
                f"Missing terms in syllogistic form: {', '.join(missingterms)}"
            )
        # Check that we have a well-formed syllogism
        if (not self._form.majorterm) or (not self._form.minorterm) or (not self._form.middleterm):
            self._structuralvalidation = ValidationResult(
                ValidationResultStatus.INVALID,
                "Missing terms in syllogistic form"
            )
            return
        # Check that the major premise is universal
        if self.majorpremise.type != StatementType.UNIVERSAL:
            self._structuralvalidation = ValidationResult(
                ValidationResultStatus.INVALID,
                "Major premise must be universl"
            )
            return
        if (
            (not self.minorpremise.subjects)
            or
            (not self.conclusion.subjects)
            or
            (self.minorpremise.subjects[0].lemma != self.conclusion.subjects[0].lemma)
        ):
            self._structuralvalidation = ValidationResult(
                ValidationResultStatus.INVALID,
                "Subject of minor premise must match subject of conclusion"
            )
            return

        # Check that major premise predicate matches conclusion predicate
        majorpred = None
        if self.majorpremise.predicateadjectives:
            majorpred = self.majorpremise.predicateadjectives[0].lemma
        elif self.majorpremise.predicatenominatives:
            majorpred = self.majorpremise.predicatenominatives[0].lemma
        elif self.majorpremise.predicates:
            majorpred = self.majorpremise.predicates[0].lemma

        conclpred = None
        if self.conclusion.predicateadjectives:
            conclpred = self.conclusion.predicateadjectives[0].lemma
        elif self.conclusion.predicatenominatives:
            conclpred = self.conclusion.predicatenominatives[0].lemma
        elif self.conclusion.predicates:
            conclpred = self.conclusion.predicates[0].lemma

        if majorpred != conclpred:
            self._structuralvalidation = ValidationResult(
                ValidationResultStatus.INVALID,
                "Predicate of major premise must match predicate of conclusion"
            )
            return
        self._structuralvalidation = ValidationResult(
            ValidationResultStatus.VALID,
            "Syllogism structure is valid"
        )

    def _validatesemantics(self) -> None:
        """Validate the semantic relationships in the syllogism."""
        # In a valid syllogism:
        # 1. The major premise should establish a SUBSET or ATTRIBUTION relationship
        # 2. The minor premise should establish an INSTANCEOF or IDENTITY relationship

        # Check major premise relationship
        majorvalid = False
        for relationship in self.majorpremise._relationships:
            if relationship in [RelationshipType.SUBSET, RelationshipType.ATTRIBUTION]:
                majorvalid = True
                break
        if not majorvalid:
            self._semanticvalidation = ValidationResult(
                ValidationResultStatus.INVALID,
                "Major premise must establish SUBSET or ATTRIBUTION relationship"
            )
            return
        minorvalid = False
        for relationship in self.minorpremise._relationships:
            if relationship in [RelationshipType.INSTANCEOF, RelationshipType.IDENTITY]:
                minorvalid = True
                break
        if not minorvalid:
            self._semanticvalidation = ValidationResult(
                ValidationResultStatus.INVALID,
                "Minor premise must establish INSTANCEOF or IDENTITY relationship"
            )
            return
        self._semanticvalidation = ValidationResult(
            ValidationResultStatus.VALID,
            "Syllogism semantics are valid"
        )

    def __post_init__(self):
        if self._form is None:
            self._extractform()

        if self._structuralvalidation is None:
            self._validatestructure()

        if self._semanticvalidation is None:
            if self._structuralvalidation.isvalid:
                self._validatesemantics()
            else:
                self._semanticvalidation = ValidationResult(
                    ValidationResultStatus.INVALID,
                    "Structural validation failed, semantic validation skipped"
                )

    @property
    def form(self) -> SyllogisticForm:
        if self._form is None:
            self._extractform()
        return self._form

    @property
    def isvalid(self) -> bool:
        if self._structuralvalidation is None:
            self._validatestructure()
        if self._semanticvalidation is None:
            self._validatesemantics()
        return (self._structuralvalidation.isvalid and self._semanticvalidation.isvalid)

    @property
    def validationmessage(self) -> str:
        structmsg = str(self._structuralvalidation) if self._structuralvalidation else "Structure not validated"
        semanticmsg = str(self._semanticvalidation) if self._semanticvalidation else "Semantics not validated"
        return f"Structure: {structmsg}\nSemantics: {semanticmsg}"

    def __str__(self) -> str:
        valstr = "Valid" if self.isvalid else "Invalid"
        return (
            f"Syllogism:\n"
            f"  Major: {self.majorpremise.content}\n"
            f"  Minor: {self.minorpremise.content}\n"
            f"  Conclusion: {self.conclusion.content}\n"
            f"  {valstr}:\n"
            f"    {self.form}"
        )


class SyllogisticProcessor:

    @staticmethod
    def ProcessStatement(text: str) -> Statement:
        return Statement(text)

    @classmethod
    def ProcessSyllogism(cls, major: str, minor: str, conclusion: str) -> Syllogism:
        return Syllogism(
            cls.ProcessStatement(major),
            cls.ProcessStatement(minor),
            cls.ProcessStatement(conclusion)
        )

    @classmethod
    def ProcessSyllogisticBody(cls, text: str) -> Syllogism:
        lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
        if len(lines) < 3:
            raise ValueError("A syllogism must have at least two premises and a conclusion")
        # Assume the first line is the major premise, second is minor, third is conclusion
        # this will need to be revised later
        return cls.ProcessSyllogism(
            lines[0],
            lines[1],
            lines[2]
        )
