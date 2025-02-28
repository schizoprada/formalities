# ~/formalities/src/formalities/utils/dialog/state.py
from __future__ import annotations
import sys, importlib, typing as t
from enum import Enum, auto
from dataclasses import dataclass, field
from loguru import logger as log

class DialogStage(Enum):
    INITIALIZATION = auto()
    PROBLEMANALYSIS = auto()
    FRAMEWORKSELECTION = auto()
    TOOLEXECUTION = auto()
    REASONING = auto()
    VALIDATION = auto()
    ERRORHANDLING = auto()
    CONCLUSION = auto()

class ErrorType(Enum):
    FRAMEWORKINCOMPATIBLE = auto()
    PROPOSITIONINVALID = auto()
    TYPEERROR = auto()
    VALIDATIONFAILED = auto()
    TOOLERROR = auto()
    IMPORTERROR = auto()
    SYNTAXERROR = auto()
    EXECUTIONERROR = auto()
    UNKNOWNERROR = auto()

@dataclass
class DialogMemory:
    propositions: dict[str, t.Any] = field(default_factory=dict)
    frameworks: dict[str, t.Any] = field(default_factory=dict)
    validationresults: list[t.Any] = field(default_factory=list)
    toolcalls: list[dict[str, t.Any]] = field(default_factory=list)
    variables: dict[str, t.Any] = field(default_factory=dict)

    def addtoolcall(self, name: str, args: dict, result: t.Any, success: bool) -> None:
        self.toolcalls.append({
            "name": name,
            "args": args,
            "result": result,
            "success": success
        })

    def previoustoolcall(self, name: t.Optional[str] = None) -> t.Optional[dict]:
        if not self.toolcalls:
            return None
        if name is None:
            return self.toolcalls[-1]
        for call in reversed(self.toolcalls):
            if call["name"] == name:
                return call
        return None


    def addframework(self, name: str, framework: t.Any) -> None:
        self.frameworks[name] = framework

    def addproposition(self, name: str, proposition: t.Any) -> None:
        self.propositions[name] = proposition

    def addvalidationresult(self, result: t.Any) -> None:
        self.validationresults.append(result)

    def previousvalidationresult(self) -> t.Optional[t.Any]:
        if not self.validationresults:
            return None
        return self.validationresults[-1]

@dataclass
class DialogHistory:
    exchanges: list[dict[str, t.Any]] = field(default_factory=list)

    def addexchange(self, role: str, content: str, metadata: t.Optional[dict]=None) -> None:
        self.exchanges.append({
            "role": role,
            "content": content,
            "metadata": (metadata or {})
        })

    def previousexchange(self, role: t.Optional[str] = None) -> t.Optional[dict]:
        if not self.exchanges:
            return None
        if role is None:
            return self.exchanges[-1]
        for exchange in reversed(self.exchanges):
            if exchange["role"] == role:
                return exchange
        return None

    def listexchanges(self, count: int = 5) -> list[dict]:
        # probably add role filtration too
        return (self.exchanges[-count:] if len(self.exchanges) >= count else self.exchanges.copy())

    def clear(self) -> None:
        self.exchanges.clear()


@dataclass
class DialogState:
    stage: DialogStage = DialogStage.INITIALIZATION
    memory: DialogMemory = field(default_factory=DialogMemory)
    history: DialogHistory = field(default_factory=DialogHistory)
    error: t.Optional[tuple[ErrorType, Exception]] = None  # Now stores the exception object directly
    context: dict[str, t.Any] = field(default_factory=dict)

    def transitionto(self, newstage: DialogStage) -> None:
        oldstage = self.stage
        self.stage = newstage
        log.info(f"Dialog state transition: {oldstage.name} -> {newstage.name}")

    def seterror(self, exception: Exception) -> None:
        """Set the error state using an exception object directly"""
        errortype = self.DetectErrorType(exception)
        self.error = (errortype, exception)
        self.transitionto(DialogStage.ERRORHANDLING)
        log.error(f"Dialog error: {errortype.name} - {str(exception)}")

    def clearerror(self) -> None:
        """Clear the current error state"""
        self.error = None
        log.debug(f"Dialog error cleared")

    def addtocontext(self, key: str, val: t.Any) -> None:
        """Add a value to the context dictionary"""
        self.context[key] = val
        log.info(f"Added to context: {key}")

    def reset(self) -> None:
        """Reset the dialog state"""
        self.stage = DialogStage.INITIALIZATION
        self.memory = DialogMemory()
        self.error = None
        self.context.clear()
        log.info("Dialog state reset")

    def todict(self) -> dict:
        """Convert the dialog state to a dictionary for serialization"""
        return {
            "stage": self.stage.name,
            "error": {
                "type": self.error[0].name,
                "message": str(self.error[1]),
                "exceptiontype": type(self.error[1]).__name__
            } if self.error else None,
            "context": self.context
        } # exclude history and memory for brevity

    @classmethod
    def DetectErrorType(cls, exception: Exception) -> ErrorType:
        """
        Detect the error type from an exception object directly.
        Uses the exception type hierarchy for precise categorization.

        Args:
            exception: The exception object

        Returns:
            The detected error type
        """
        # Import-related errors
        if isinstance(exception, ImportError) or isinstance(exception, ModuleNotFoundError):
            return ErrorType.IMPORTERROR

        # Syntax errors
        if isinstance(exception, SyntaxError):
            return ErrorType.SYNTAXERROR

        # Type errors
        if isinstance(exception, TypeError):
            return ErrorType.TYPEERROR

        # Check for custom framework errors
        if (excname:=type(exception).__name__).endswith('ValidationError') or (excname == 'ValidationException'):
            return ErrorType.VALIDATIONFAILED

        if (excname.endswith('FrameworkError')) or (excname == 'FrameworkException'):
            return ErrorType.FRAMEWORKINCOMPATIBLE

        if (excname.endswith('PropositionError')) or (excname == 'PropositionException'):
            return ErrorType.PROPOSITIONINVALID

        # Execution errors
        if isinstance(exception, (NameError, AttributeError, ValueError, IndexError, KeyError)):
            return ErrorType.EXECUTIONERROR

        # Default to unknown error
        return ErrorType.UNKNOWNERROR
