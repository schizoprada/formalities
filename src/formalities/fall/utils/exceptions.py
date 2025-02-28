# ~/formalities/src/formalities/fall/utils/exceptions.py
"""Custom exceptions for the FALL language."""

class FALLException(Exception):
    """Base exception class for all FALL exceptions."""
    pass

class ValidationException(FALLException):
    """Exception raised for validation errors."""
    pass

class FrameworkException(FALLException):
    """Exception raised for framework-related errors."""
    pass

class PropositionException(FALLException):
    """Exception raised for proposition-related errors."""
    pass

class ParsingException(FALLException):
    """Exception raised for parsing errors."""
    pass

class ExecutionException(FALLException):
    """Exception raised for execution errors."""
    pass
