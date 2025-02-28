# ~/formalities/src/formalities/utils/dialog/strategies/correction.py
from __future__ import annotations
import typing as t
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from formalities.utils.dialog.controller import DialogStrategy, DialogRequest, DialogResponse, DialogAction
from formalities.utils.dialog.state import DialogState, DialogStage, ErrorType
from formalities.utils.dialog.patterns.errors import ErrorContextProvider, ErrorContext
from formalities.utils.discovery import frameworkregistry
from loguru import logger as log


class ErrorCorrectionStrategy(DialogStrategy):
    """
    Base strategy for handling errors in the dialog flow.
    Focuses on providing context and validation information without prescribing solutions.
    """

    @property
    def name(self) -> str:
        return "ErrorCorrectionStrategy"

    @property
    def handleablestages(self) -> list[DialogStage]:
        return [DialogStage.ERRORHANDLING]

    def apply(self, state: DialogState, request: DialogRequest) -> DialogResponse:
        """Apply the error correction strategy based on error type"""
        if not state.error:
            log.warning("ErrorCorrectionStrategy called but no error in state")
            return DialogResponse(
                content="Sorry, I encountered an issue with error handling.",
                action=DialogAction.FALLBACK
            )

        errortype, exception = state.error
        log.debug(f"ErrorCorrectionStrategy handling {errortype.name} error")

        # Get error context
        errorcontext = ErrorContextProvider.getcontext(state)
        if not errorcontext:
            return DialogResponse(
                content=f"An error occurred: {str(exception)}",
                action=DialogAction.FALLBACK
            )

        # Dispatch to specialized handler based on error type
        if errortype == ErrorType.IMPORTERROR:
            return self._handleimporterror(state, errorcontext)
        elif errortype == ErrorType.TYPEERROR:
            return self._handletypeerror(state, errorcontext)
        elif errortype == ErrorType.SYNTAXERROR:
            return self._handlesyntaxerror(state, errorcontext)
        elif errortype == ErrorType.FRAMEWORKINCOMPATIBLE:
            return self._handleframeworkerror(state, errorcontext)
        elif errortype == ErrorType.PROPOSITIONINVALID:
            return self._handlepropositionerror(state, errorcontext)
        else:
            return self._handlegenericerror(state, errorcontext)

    def _handleimporterror(self, state: DialogState, errorcontext: ErrorContext) -> DialogResponse:
        """Handle import errors by providing information about available components"""
        message = [
            f"I noticed you're trying to import a component that isn't available: {errorcontext.message}",
            "",
            "Here are some components that might be relevant:"
        ]

        # Add suggested components
        if errorcontext.relatedcomponents:
            for comp in errorcontext.relatedcomponents:
                message.append(f"- {comp.name} ({comp.typeof}): Import from {comp.modulepath}")
        else:
            message.append("- No directly relevant components found.")

        # Add general suggestions
        message.extend([
            "",
            "To explore available components, you could:",
            "1. Use the matchmaker tool to discover components",
            "2. Check formalities.core.types.propositions for available proposition types",
            "3. Check formalities.core.types.operators for logical operators"
        ])

        # Add error context
        message.extend([
            "",
            "Error details:",
            f"- Type: {errorcontext.exceptiontype}",
            f"- Message: {errorcontext.message}"
        ])

        return DialogResponse(
            content="\n".join(message),
            action=DialogAction.RETRY,
            suggestedtools=["matchmaker"]
        )

    def _handletypeerror(self, state: DialogState, errorcontext: ErrorContext) -> DialogResponse:
        """Handle type errors by providing interface information"""
        message = [
            f"I noticed a type mismatch: {errorcontext.message}",
            "",
            "This usually means the object you're using doesn't match the expected interface."
        ]

        # Extract specific type information if available
        typeanalysis = ErrorContextProvider.geterroranalysis(state.error[1], state.error[0])
        if "providedtype" in typeanalysis and "expectedtype" in typeanalysis:
            message.extend([
                "",
                f"Provided type: {typeanalysis['providedtype']}",
                f"Expected type: {typeanalysis['expectedtype']}"
            ])

        # Add component suggestions
        if errorcontext.relatedcomponents:
            message.append("")
            message.append("Here are components that might be compatible:")
            for comp in errorcontext.relatedcomponents:
                message.append(f"- {comp.name}: {comp.description.split('.')[0]}")

        # General advice
        message.extend([
            "",
            "Consider:",
            "1. Checking the method signatures and required parameters",
            "2. Validating object types before passing them to functions",
            "3. Using appropriate type conversion where needed"
        ])

        return DialogResponse(
            content="\n".join(message),
            action=DialogAction.RETRY,
            suggestedtools=["matchmaker"]
        )

    def _handlesyntaxerror(self, state: DialogState, errorcontext: ErrorContext) -> DialogResponse:
        """Handle syntax errors in user code"""
        message = [
            f"I found a syntax error: {errorcontext.message}",
            "",
            "This often happens due to:"
        ]

        # Look for specific syntax patterns
        errorstr = errorcontext.message.lower()
        if "unexpected indent" in errorstr:
            message.append("- Inconsistent indentation (check spaces vs tabs)")
        elif "unexpected eof" in errorstr:
            message.append("- Missing closing parenthesis, bracket, or quote")
        elif "invalid syntax" in errorstr:
            message.append("- General syntax issue (missing comma, colon, etc.)")
        else:
            message.append("- General syntax issue")

        # Add context from the error
        if errorcontext.traceback:
            lines = errorcontext.traceback.split("\n")
            for line in lines:
                if "^" in line:  # The pointer to error location
                    index = lines.index(line)
                    if index > 0:
                        message.extend([
                            "",
                            "The error appears to be here:",
                            f"```python",
                            lines[index-1],  # Code line
                            line,            # Pointer
                            f"```"
                        ])
                    break

        # General advice
        message.extend([
            "",
            "Try:",
            "1. Checking indentation and line endings",
            "2. Ensuring all brackets and quotes are properly closed",
            "3. Verifying that all statements end with proper punctuation"
        ])

        return DialogResponse(
            content="\n".join(message),
            action=DialogAction.RETRY
        )

    def _handleframeworkerror(self, state: DialogState, errorcontext: ErrorContext) -> DialogResponse:
        """Handle framework incompatibility errors"""
        message = [
            f"I found a framework compatibility issue: {errorcontext.message}",
            "",
            "This occurs when a proposition or operation isn't supported by the chosen framework."
        ]

        # Add framework suggestions
        if errorcontext.relatedcomponents:
            frameworks = [c for c in errorcontext.relatedcomponents if c.typeof == "framework"]
            if frameworks:
                message.append("")
                message.append("Here are alternative frameworks that might support your needs:")
                for fw in frameworks:
                    message.append(f"- {fw.name}: {fw.description.split('.')[0]}")

        # Add validation context
        if errorcontext.validationcontext:
            message.append("")
            message.append("Validation context:")
            for key, value in errorcontext.validationcontext.items():
                message.append(f"- {key}: {value}")

        # General suggestions
        message.extend([
            "",
            "Consider:",
            "1. Using a different logical framework",
            "2. Adapting your proposition to fit framework constraints",
            "3. Creating a composite framework to handle mixed operations"
        ])

        return DialogResponse(
            content="\n".join(message),
            action=DialogAction.RETRY,
            suggestedtools=["matchmaker"]
        )

    def _handlepropositionerror(self, state: DialogState, errorcontext: ErrorContext) -> DialogResponse:
        """Handle errors related to invalid propositions"""
        message = [
            f"I found an issue with the proposition: {errorcontext.message}",
            "",
            "This typically happens when a proposition doesn't meet validation criteria."
        ]

        # Add proposition type suggestions
        proptypes = []
        for comp in errorcontext.relatedcomponents:
            if "Proposition" in comp.name:
                proptypes.append(comp)

        if proptypes:
            message.append("")
            message.append("Here are proposition types that might be appropriate:")
            for prop in proptypes:
                message.append(f"- {prop.name}: {prop.description.split('.')[0]}")

        # Add validation context
        if errorcontext.validationcontext:
            message.append("")
            message.append("Validation context:")
            for key, value in errorcontext.validationcontext.items():
                message.append(f"- {key}: {value}")

        # General advice
        message.extend([
            "",
            "Consider:",
            "1. Checking the proposition structure",
            "2. Verifying all components are properly validated",
            "3. Using appropriate proposition types for your data"
        ])

        return DialogResponse(
            content="\n".join(message),
            action=DialogAction.RETRY,
            suggestedtools=["matchmaker"]
        )

    def _handlegenericerror(self, state: DialogState, errorcontext: ErrorContext) -> DialogResponse:
        """Handle general errors when specific handlers aren't available"""
        message = [
            f"I encountered an error: {errorcontext.message}",
            "",
            f"Error type: {errorcontext.exceptiontype}"
        ]

        # Add suggestions from error context
        if errorcontext.suggestions:
            message.append("")
            message.append("Here are some suggestions:")
            for suggestion in errorcontext.suggestions:
                message.append(f"- {suggestion}")

        # Add related components
        if errorcontext.relatedcomponents:
            message.append("")
            message.append("Related components that might be helpful:")
            for comp in errorcontext.relatedcomponents:
                message.append(f"- {comp.name} ({comp.typeof})")

        # General guidance
        message.extend([
            "",
            "I can help you troubleshoot this issue. Would you like to:",
            "1. Explore available components with the matchmaker tool",
            "2. Try a different approach",
            "3. Get more detailed information about specific components"
        ])

        return DialogResponse(
            content="\n".join(message),
            action=DialogAction.RETRY,
            suggestedtools=["matchmaker"]
        )


class ImportErrorStrategy(ErrorCorrectionStrategy):
    """Specialized strategy for import errors"""

    @property
    def name(self) -> str:
        return "ImportErrorStrategy"

    def apply(self, state: DialogState, request: DialogRequest) -> DialogResponse:
        if not state.error or state.error[0] != ErrorType.IMPORTERROR:
            return super().apply(state, request)

        errorcontext = ErrorContextProvider.getcontext(state)
        return self._handleimporterror(state, errorcontext)


class TypeErrorStrategy(ErrorCorrectionStrategy):
    """Specialized strategy for type errors"""

    @property
    def name(self) -> str:
        return "TypeErrorStrategy"

    def apply(self, state: DialogState, request: DialogRequest) -> DialogResponse:
        if not state.error or state.error[0] != ErrorType.TYPEERROR:
            return super().apply(state, request)

        errorcontext = ErrorContextProvider.getcontext(state)
        return self._handletypeerror(state, errorcontext)


class SyntaxErrorStrategy(ErrorCorrectionStrategy):
    """Specialized strategy for syntax errors"""

    @property
    def name(self) -> str:
        return "SyntaxErrorStrategy"

    def apply(self, state: DialogState, request: DialogRequest) -> DialogResponse:
        if not state.error or state.error[0] != ErrorType.SYNTAXERROR:
            return super().apply(state, request)

        errorcontext = ErrorContextProvider.getcontext(state)
        return self._handlesyntaxerror(state, errorcontext)


class FrameworkErrorStrategy(ErrorCorrectionStrategy):
    """Specialized strategy for framework compatibility errors"""

    @property
    def name(self) -> str:
        return "FrameworkErrorStrategy"

    def apply(self, state: DialogState, request: DialogRequest) -> DialogResponse:
        if not state.error or state.error[0] != ErrorType.FRAMEWORKINCOMPATIBLE:
            return super().apply(state, request)

        errorcontext = ErrorContextProvider.getcontext(state)
        return self._handleframeworkerror(state, errorcontext)


class PropositionErrorStrategy(ErrorCorrectionStrategy):
    """Specialized strategy for proposition validation errors"""

    @property
    def name(self) -> str:
        return "PropositionErrorStrategy"

    def apply(self, state: DialogState, request: DialogRequest) -> DialogResponse:
        if not state.error or state.error[0] != ErrorType.PROPOSITIONINVALID:
            return super().apply(state, request)

        errorcontext = ErrorContextProvider.getcontext(state)
        return self._handlepropositionerror(state, errorcontext)


class RecoverableErrorHandler:
    """
    Utility for registering error handling strategies with a controller.
    Covers common error types with specialized handlers.
    """

    @staticmethod
    def register(controller) -> None:
        """Register all error handling strategies with the controller"""
        # Register general handler
        controller.registerstrategy(ErrorCorrectionStrategy())

        # Register specialized handlers
        controller.registerstrategy(ImportErrorStrategy())
        controller.registerstrategy(TypeErrorStrategy())
        controller.registerstrategy(SyntaxErrorStrategy())
        controller.registerstrategy(FrameworkErrorStrategy())
        controller.registerstrategy(PropositionErrorStrategy())

        #log.info("Registered error handling strategies")
