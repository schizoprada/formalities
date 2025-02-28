# ~/formalities/src/formalities/utils/dialog/management.py
from __future__ import annotations
import typing as t
from dataclasses import dataclass, field
from formalities.utils.dialog.state import DialogState, DialogStage, ErrorType
from loguru import logger as log


@dataclass
class ErrorPattern:
    """Pattern to detect in error sequences"""
    errortypes: list[ErrorType]
    count: int = 1
    timewindow: int = 5  # Number of interactions to consider


@dataclass
class RecoveryPath:
    """Tracks a sequence of actions to recover from errors"""
    initialerrortype: ErrorType
    steps: list[dict] = field(default_factory=list)
    resolved: bool = False

    def addstep(self, action: str, result: bool, context: dict = None) -> None:
        """Add a recovery step"""
        self.steps.append({
            "action": action,
            "result": result,
            "context": context or {}
        })

    def markcomplete(self) -> None:
        """Mark this recovery path as successfully resolved"""
        self.resolved = True

    @property
    def duration(self) -> int:
        """Get the number of steps in this recovery path"""
        return len(self.steps)


class StateManager:
    """
    Manages dialog state transitions and detects patterns in errors
    to improve error recovery.
    """

    def __init__(self, state: DialogState):
        self.state = state
        self.errorpatterns = {}  # Pattern name -> ErrorPattern
        self.recoveryhistory: list[RecoveryPath] = []
        self.currentrecovery: t.Optional[RecoveryPath] = None
        self._originaltransition = None  # Store original transition method

        # Register common error patterns
        self._registercommonpatterns()

    def _registercommonpatterns(self) -> None:
        """Register common error patterns to detect"""
        self.errorpatterns["repeatedimport"] = ErrorPattern(
            [ErrorType.IMPORTERROR],
            count=2,
            timewindow=3
        )

        self.errorpatterns["typeafterimport"] = ErrorPattern(
            [ErrorType.IMPORTERROR, ErrorType.TYPEERROR],
            count=1,
            timewindow=2
        )

        self.errorpatterns["validationcycle"] = ErrorPattern(
            [ErrorType.PROPOSITIONINVALID, ErrorType.FRAMEWORKINCOMPATIBLE],
            count=1,
            timewindow=3
        )

    def detecterrorpatterns(self) -> list[str]:
        """
        Detect patterns in recent errors.

        Returns:
            List of detected pattern names
        """
        if not self.state.error:
            return []

        detected = []
        recentcalls = self.state.memory.toolcalls[-10:] if len(self.state.memory.toolcalls) > 0 else []

        # Extract error types from recent failures
        recenterrortypes = []
        for call in recentcalls:
            if not call["success"] and "exception" in call["result"]:
                errortype = self.state.DetectErrorType(call["result"]["exception"])
                recenterrortypes.append(errortype)

        # Check each pattern
        for name, pattern in self.errorpatterns.items():
            window = recenterrortypes[-pattern.timewindow:] if len(recenterrortypes) >= pattern.timewindow else recenterrortypes

            # Simple repeated error check
            if len(pattern.errortypes) == 1 and pattern.errortypes[0] in window:
                if window.count(pattern.errortypes[0]) >= pattern.count:
                    detected.append(name)

            # Sequence pattern check
            elif len(pattern.errortypes) > 1:
                # Check if the sequence appears in the window
                for i in range(len(window) - len(pattern.errortypes) + 1):
                    if window[i:i+len(pattern.errortypes)] == pattern.errortypes:
                        detected.append(name)
                        break

        return detected

    def handleerrorpattern(self, pattern: str) -> None:
        """
        Handle a detected error pattern with specialized approach.

        Args:
            pattern: Name of the detected pattern
        """
        log.info(f"Handling error pattern: {pattern}")

        if pattern == "repeatedimport":
            # Suggest broader component suggestions
            self.state.context["broadensuggestions"] = True
            self.state.context["suggestiondepth"] = 2

        elif pattern == "typeafterimport":
            # Focus on interface compatibility
            self.state.context["focusoninterface"] = True

        elif pattern == "validationcycle":
            # Suggest alternative frameworks
            self.state.context["suggestalternativeframework"] = True

    def trackrecovery(self) -> None:
        """Track the current error recovery process"""
        if self.state.error and not self.currentrecovery:
            # New error, start tracking recovery
            errortype, _ = self.state.error
            self.currentrecovery = RecoveryPath(initialerrortype=errortype)
            log.debug(f"Started tracking recovery for {errortype.name}")

        elif not self.state.error and self.currentrecovery:
            # Error resolved, complete recovery path
            self.currentrecovery.markcomplete()
            self.recoveryhistory.append(self.currentrecovery)
            self.currentrecovery = None
            log.debug(f"Completed recovery path")

    def addrecoverystep(self, action: str, result: bool, context: dict = None) -> None:
        """
        Add a step to the current recovery process.

        Args:
            action: Action taken (e.g., "suggestion", "tool_call")
            result: Whether the action was successful
            context: Additional context about the action
        """
        if self.currentrecovery:
            self.currentrecovery.addstep(action, result, context)
            log.debug(f"Added recovery step: {action}, success={result}")

    def handlestatetransition(self, newstage: DialogStage) -> None:
        """
        Handle state transitions with appropriate logic.

        Args:
            newstage: The new dialog stage to transition to
        """
        oldstage = self.state.stage

        # Special handling for certain transitions
        if oldstage == DialogStage.ERRORHANDLING and newstage != DialogStage.ERRORHANDLING:
            # Transitioning out of error handling
            if self.currentrecovery:
                self.currentrecovery.markcomplete()
                self.recoveryhistory.append(self.currentrecovery)
                self.currentrecovery = None

        elif newstage == DialogStage.ERRORHANDLING:
            # Transitioning to error handling
            patterns = self.detecterrorpatterns()
            for pattern in patterns:
                self.handleerrorpattern(pattern)

            # Start tracking recovery
            self.trackrecovery()


# Create a global manager instance
statemanager = StateManager(None)

def initialize(state: DialogState) -> None:
    """Initialize the state manager with a dialog state"""
    global statemanager
    statemanager = StateManager(state)
    statemanager.state = state

    # Store original transition method
    original_transition = state.transitionto
    statemanager._originaltransition = original_transition

    # Define the enhanced transition function
    def enhancedtransition(newstage: DialogStage) -> None:
        """Enhanced transition that uses state manager logic"""
        # Process transition with state manager
        statemanager.handlestatetransition(newstage)

        # Call original transition method to avoid recursion
        oldstage = state.stage
        state.stage = newstage  # Directly set the stage
        log.info(f"Dialog state transition: {oldstage.name} -> {newstage.name}")

    # Replace the method
    state.transitionto = enhancedtransition
    #log.info("Initialized state manager")
