# ~/formalities/src/formalities/utils/integrations.py
from __future__ import annotations
import typing as t
from formalities.utils.dialog.controller import dialogcontroller, DialogRequest, DialogResponse, DialogAction
from formalities.utils.dialog.strategies.correction import RecoverableErrorHandler
from formalities.utils.toolcalls import toolcallhandler, ToolCallRequest, ToolCallResponse
from formalities.frameworks.base import ValidationResult
from formalities.utils.frameworks import frameworkselector
from loguru import logger as log


def initializecontrollerstrategies() -> None:
    """Initialize the dialog controller with error handling strategies"""
    # Register all error correction strategies
    RecoverableErrorHandler.register(dialogcontroller)
    log.info("Initialized dialog controller strategies")


def integratetoolhandler() -> None:
    """
    Connect the dialog controller to tool call handler.
    This overrides the controller's handletoolcall method to use the shared toolcallhandler.
    """
    # Store original references
    originalmatchmaker = toolcallhandler._matchmaker
    originalmethodbuilder = toolcallhandler._methodbuilder

    # Fix: Create a correct handletoolcall method for the dialog controller
    def enhancedhandletoolcall(name: str, args: dict) -> t.Any:
        """Enhanced handletoolcall that routes to the appropriate handler"""
        try:
            response = None
            if name == "matchmaker":
                response = toolcallhandler._matchmaker(args)
            elif name == "methodbuilder":
                response = toolcallhandler._methodbuilder(args)
            else:
                raise ValueError(f"Unknown tool: {name}")

            rdata = response.data if response.success else {"error": response.error}
            dialogcontroller.state.memory.addtoolcall(name, args, rdata, response.success)

            if not response.success:
                if response.exception:
                    dialogcontroller.state.seterror(response.exception)
                else:
                    dialogcontroller.state.seterror(Exception(response.error))
                return {"error": response.error}

            return response.data
        except Exception as e:
            log.error(f"Error executing tool call: {name}")
            dialogcontroller.state.seterror(e)
            return {"error": f"Tool execution error: {str(e)}"}

    # Replace the dialogcontroller's handletoolcall with our enhanced version
    dialogcontroller.handletoolcall = enhancedhandletoolcall

    log.info("Integrated tool handler with dialog controller")


def integratevaliationresults() -> None:
    """
    Integrate validation results with dialog state.
    This enhances the ValidationResult class to update dialog state when validation fails.
    """
    # Store the original ValidationResult.__init__
    originalinit = ValidationResult.__init__

    def enhancedinit(self, isvalid: bool, errors: list[str] = None):
        """Enhanced init that updates dialog state"""
        originalinit(self, isvalid, errors if errors is not None else [])

        if not isvalid and errors:
            from formalities.utils.dialog.state import ErrorType
            from formalities.validation.base import ValidationError

            # Create a ValidationError with the validation errors
            error = ValidationError("; ".join(errors))

            # Update dialog state with the error
            try:
                dialogcontroller.state.seterror(error)
            except Exception as e:
                log.error(f"Failed to update dialog state with validation error: {str(e)}")

    # Replace the __init__ method
    ValidationResult.__init__ = enhancedinit
    log.info("Integrated validation results with dialog state")


def integrateframeworkselection() -> None:
    """
    Integrate framework selection with dialog controller.
    Enhances the dialog state to track framework selection.
    """
    # Capture the original suggest method
    originalsuggest = frameworkselector.suggest

    def enhancedsuggest(*args, **kwargs):
        """Enhanced suggest that updates dialog state"""
        suggestions = originalsuggest(*args, **kwargs)

        if suggestions:
            # Add top framework suggestions to dialog state
            dialogcontroller.state.context["frameworksuggestions"] = [
                {
                    "name": suggestion.framework.name,
                    "compatibility": suggestion.compatibility,
                    "missing_features": suggestion.missingfeatures,
                    "notes": suggestion.notes
                }
                for suggestion in suggestions[:3]  # Top 3 suggestions
            ]

        return suggestions

    # Replace with enhanced version
    frameworkselector.suggest = enhancedsuggest
    log.info("Integrated framework selection with dialog controller")


def integratestatemanagement() -> None:
    """Integrate state management with dialog controller"""
    from formalities.utils.dialog.management import initialize

    # Check if we already initialized
    if hasattr(dialogcontroller.state, 'transitionto'):
        originalfunction = dialogcontroller.state.transitionto.__name__
        if originalfunction == 'enhancedtransition':
            log.info("State management already initialized, skipping")
            return

    initialize(dialogcontroller.state)
    log.info("Integrated state management with dialog controller")


def setupintegrations() -> None:
    """Set up all integrations"""
    initializecontrollerstrategies()
    integratetoolhandler()
    integratevaliationresults()
    integrateframeworkselection()
    integratestatemanagement()
    log.info("All integrations completed")


# Always initialize when this module is imported
setupintegrations()
