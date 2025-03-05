# ~/formalities/src/formalities/fall/bridges/valium.py
from __future__ import annotations
import typing as t
from dataclasses import dataclass, field
from formalities.core.types.propositions import (
    Proposition, AtomicProposition, CompoundProposition
)
from formalities.core.types.operators import (
    AND, OR, NOT, IMPLIES, IFF
)
from formalities.core.types.logic import LogicType
from formalities.frameworks.base import ValidationResult
from formalities.fall.core.types.language.common import (
    WordType, WordFunction, RelationshipType, StatementType
)
from formalities.fall.core.types.language.base import (
    Word, Statement
)
from formalities.fall.core.types.language.syllogistic import (
    Syllogism, SyllogisticProcessor, ValidationResultStatus
)
from formalities.fall.utils.exceptions import ValidationException
from loguru import logger as log

@dataclass
class ValiumAnalysisResult:
    success: bool
    typesofstatements: t.List[StatementType] = field(default_factory=list)
    relationships: t.List[RelationshipType] = field(default_factory=list)
    subjects: t.List[str] = field(default_factory=list)
    predicates: t.List[str] = field(default_factory=list)
    propositions: t.List[Proposition] = field(default_factory=list)
    syllogism: t.Optional[Syllogism] = None
    error: t.Optional[str] = None
    confidence: float = 1.0


class ValiumBridge:
    """
    Bridge between FALL language constructs and the VALIUM language processing system.
    Provides natural language understanding capabilities for logic validation.
    """
    def __int__(self, enablesyl: bool = True):
        self.enabled = False
        self._enablesyl = enablesyl
        self._statements = {}
        self._syllogisms = {}

    def enable(self) -> str:
        self.enabled = True
        return "VALIUM Bridge Enabled"

    def disable(self) -> str:
        self.enabled = False
        return "VALIUM Bridge Disabled"

    def _createpropositionsfromstatement(self, statement: Statement) -> t.List[Proposition]:
        propositions = []
        try:
            if statement.type == StatementType.UNIVERSAL:
                if statement.subjects and (statement.predicateadjectives or statement.predicatenominatives):
                    subject = statement.subjects[0].content
                    predicate = None
                    if statement.predicateadjectives:
                        predicate = statement.predicateadjectives[0].content
                    elif statement.predicatenominatives:
                        predicate = statement.predicatenominatives[0].content
                    if predicate:
                        xprop = AtomicProposition(subject)
                        yprop = AtomicProposition(predicate)
                        uprop = CompoundProposition(
                            IMPLIES(),
                            (xprop, yprop)
                        )
                        propositions.append(uprop)
            elif statement.type == StatementType.DECLARATIVE:
                if statement.subjects and (statement.predicateadjectives or statement.predicatenominatives):
                    subject = statement.subjects[0].content
                    predicate = None
                    if statement.predicateadjectives:
                        predicate = statement.predicateadjectives[0].content
                    elif statement.predicatenominatives:
                        predicate = statement.predicatenominatives[0].content
                    if predicate:
                        subjprop = AtomicProposition(subject)
                        predprop = AtomicProposition(predicate)
                        rel = statement.primaryrelationship
                        if (rel == RelationshipType.IDENTITY) or (rel == RelationshipType.INSTANCEOF):
                            idprop = CompoundProposition(
                                IFF(),
                                (subjprop, predprop)
                            )
                            propositions.append(idprop)
                        else:
                            propertyprop = CompoundProposition(
                                AND(),
                                (subjprop, predprop)
                            )
                            propositions.append(propertyprop)
            # other statement types to be handled...
        except Exception as e:
            log.error(f"Error Creating Proposition: {str(e)}")
        return propositions

    def analyzestatement(self, text: str) -> ValiumAnalysisResult:
        if not self.enabled:
            return ValiumAnalysisResult(
                success=False,
                error="VALIUM Bridge is disabled"
            )
        try:
            statement = Statement(text)
            self._statements[text] = statement

            relationships = statement._relationships if statement._relationships else []

            subjects = [w.content for w in statement.subjects]
            predicates = []
            if statement.predicates:
                predicates.extend([w.content for w in statement.predicates])
            if statement.predicatenominatives:
                predicates.extend([w.content for w in statement.predicatenominatives])
            if statement.predicateadjectives:
                predicates.extend([w.content for w in statement.predicateadjectives])

            propositions = self._createpropositionsfromstatement(statement)
            return ValiumAnalysisResult(
                success=True,
                typesofstatements=[statement.type],
                relationships=relationships,
                subjects=subjects,
                predicates=predicates,
                propositions=propositions
            )
        except Exception as e:
            log.error(f"Error Analyzing Statement: {str(e)}")
            return ValiumAnalysisResult(
                success=False,
                error=f"Analysis Error: {str(e)}"
            )

    def analyzesyllogism(self, major: str, minor: str, conclusion: str) -> ValiumAnalysisResult:
        if not self.enabled:
            return ValiumAnalysisResult(
                success=False,
                error=f"VALIUM Bridge Disabled"
            )
        if not self._enablesyl:
            return ValiumAnalysisResult(
                success=False,
                error=f"Syllogistic Reasoning Not Enabled"
            )
        try:
            syllogism = SyllogisticProcessor.ProcessSyllogism(major, minor, conclusion)
            key = f"|".join([major, minor, conclusion])
            self._syllogisms[key] = syllogism
            typesofstatements = [
                syllogism.majorpremise.type,
                syllogism.minorpremise.type,
                syllogism.conclusion.type
            ]
            relationships = (
                (syllogism.majorpremise._relationships or []) +
                (syllogism.minorpremise._relationships or []) +
                (syllogism.conclusion._relationships or [])
            )
            subjects = []
            if syllogism.majorpremise.subjects:
                subjects.extend([w.content for w in syllogism.majorpremise.subjects])
            if syllogism.minorpremise.subjects:
                subjects.extend([w.content for w in syllogism.minorpremise.subjects])
            if syllogism.conclusion.subjects:
                subjects.extend([w.content for w in syllogism.conclusion.subjects])
            predicates = []
            for stmt in [syllogism.majorpremise, syllogism.minorpremise, syllogism.conclusion]:
                if stmt.predicates:
                    predicates.extend([w.content for w in stmt.predicates])
                if stmt.predicatenominatives:
                    predicates.extend([w.content for w in stmt.predicatenominatives])
                if stmt.predicateadjectives:
                    predicates.extend([w.content for w in stmt.predicateadjectives])
            majorprops = self._createpropositionsfromstatement(syllogism.majorpremise)
            minorprops = self._createpropositionsfromstatement(syllogism.minorpremise)
            conclusionprops = self._createpropositionsfromstatement(syllogism.conclusion)
            propositions = (majorprops + minorprops + conclusionprops)
            return ValiumAnalysisResult(
                success=syllogism.isvalid,
                typesofstatements=typesofstatements,
                relationships=relationships,
                subjects=subjects,
                predicates=predicates,
                propositions=propositions,
                syllogism=syllogism,
                error=(None if syllogism.isvalid else syllogism.validationmessage)
            )
        except Exception as e:
            log.error(f"Error Analyzing Syllogism: {str(e)}")
            return ValiumAnalysisResult(
                success=False,
                error=f"Analysis Error: {str(e)}"
            )

    def validateinference(self, premises: t.List[str], conclusion: str) -> ValidationResult:
        if not self.enabled:
            return ValidationResult(
                isvalid=False,
                errors=["VALIUM Bridge is Disabled"]
            )
        if not self._enablesyl:
            return ValidationResult(
                isvalid=False,
                errors=["Syllogistic reasoning is not enabled"]
            )
        if len(premises) == 2:
            try:
                result = self.analyzesyllogism(premises[0], premises[1], conclusion)
                if result.success:
                    return ValidationResult(
                        isvalid=True,
                        errors=[]
                    )
                return ValidationResult(
                    isvalid=False,
                    errors=[result.error] if result.error else ["Invalid Inference"]
                )
            except Exception as e:
                log.error(f"Error Validating Inference: {str(e)}")
                return ValidationResult(
                    isvalid=False,
                    errors=[f"Validation Error: {str(e)}"]
                )
        # more complex scenarios pending implementation
        return ValidationResult(
            isvalid=False,
            errors=["Complex Inference Validation Not Yet Implemented"]
        )
