# ~/formalities/src/formalities/utils/dialog/patterns/errors.py
from __future__ import annotations
import re, inspect, traceback, typing as t
from dataclasses import dataclass, field
from importlib import import_module
from pathlib import Path
from formalities.utils.dialog.state import DialogState, ErrorType
from formalities.utils.discovery import frameworkregistry, ComponentInfo
from loguru import logger as log


@dataclass
class ErrorContext:
    """
    Context information about an error, providing validation context
    without prescribing specific solutions.
    """
    errortype: ErrorType
    message: str
    exceptiontype: str
    traceback: str
    relatedcomponents: list[ComponentInfo] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    validationcontext: dict[str, t.Any] = field(default_factory=dict)


class ErrorAnalyzer:
    """
    Analyzes exceptions to extract relevant information and context
    without prescribing specific fixes.
    """

    @staticmethod
    def extractframeworkcomponents(exception: Exception) -> list[ComponentInfo]:
        """
        Extract potentially relevant framework components based on the exception.

        This provides context about available components without prescribing
        specific implementations.
        """
        components = []
        errorstr = str(exception)

        # Extract keywords that might be relevant to the error
        keywords = set()

        # Add exception type as a keyword
        keywords.add(type(exception).__name__.lower().replace('error', ''))

        # Extract potential class/module names from error message
        classpattern = r'\'([A-Za-z0-9_]+)\'|\"([A-Za-z0-9_]+)\"|`([A-Za-z0-9_]+)`'
        for match in re.finditer(classpattern, errorstr):
            matched = match.group(1) or match.group(2) or match.group(3)
            if matched:
                keywords.add(matched.lower())

        # If it's an ImportError or ModuleNotFoundError, extract the module name
        if isinstance(exception, ImportError) or isinstance(exception, ModuleNotFoundError):
            # Pattern to match "No module named 'X'" or similar
            modulepattern = r'[\'"]([A-Za-z0-9_\.]+)[\'"]'
            matches = re.findall(modulepattern, errorstr)
            for match in matches:
                parts = match.split('.')
                for part in parts:
                    keywords.add(part.lower())

        # If it's a TypeError, extract potential type names
        if isinstance(exception, TypeError):
            # Look for type names in the error message
            typepattern = r'([A-Za-z0-9_]+) object'
            matches = re.findall(typepattern, errorstr)
            for match in matches:
                keywords.add(match.lower())

        # Query framework registry for relevant components
        for keyword in keywords:
            if len(keyword) > 3:  # Avoid very short keywords
                components.extend(frameworkregistry.query(keyword=keyword))

        # Deduplicate and return
        uniquecomponents = []
        seen = set()
        for component in components:
            if component.name not in seen:
                seen.add(component.name)
                uniquecomponents.append(component)

        return uniquecomponents[:5]  # Limit to top 5 most relevant

    @staticmethod
    def extractvalidationcontext(exception: Exception) -> dict[str, t.Any]:
        """
        Extract validation context from the exception to provide
        information about what constraints were violated.
        """
        context = {}

        # Check for validation-specific exceptions
        try:
            ValidationError = import_module('formalities.validation.base').ValidationError
            if isinstance(exception, ValidationError) and hasattr(exception, 'context'):
                return exception.context
        except (ImportError, AttributeError):
            pass

        # Try to extract validation information from the exception message
        errorstr = str(exception)

        # Look for constraint mentions
        if "requires" in errorstr:
            reqpattern = r'requires ([^.]+)'
            matches = re.findall(reqpattern, errorstr)
            if matches:
                context["requirements"] = matches

        # Look for validation errors
        if "invalid" in errorstr.lower() or "validation" in errorstr.lower():
            context["validation_error"] = errorstr

        # Add traceback information that might help understand the context
        tb = traceback.extract_tb(exception.__traceback__)
        if tb:
            # Get the module where the error occurred
            failed_module = tb[-1].filename
            context["error_location"] = {
                "file": Path(failed_module).name,
                "line": tb[-1].lineno,
                "function": tb[-1].name
            }

        return context

    @staticmethod
    def generatesuggestedcomponents(errortype: ErrorType, relatedcomponents: list[ComponentInfo]) -> list[str]:
        """
        Generate suggestions about available components that might be relevant.
        These suggestions provide information without prescribing specific implementations.
        """
        suggestions = []

        if errortype == ErrorType.IMPORTERROR:
            # For import errors, suggest available components that might be relevant
            availabletypes = set(comp.typeof for comp in relatedcomponents)
            for typename in availabletypes:
                typecomponents = [c for c in relatedcomponents if c.typeof == typename]
                if typecomponents:
                    names = [c.name for c in typecomponents]
                    suggestions.append(f"Available {typename} components include: {', '.join(names)}")

        elif errortype == ErrorType.TYPEERROR:
            # For type errors, suggest components with appropriate interfaces
            suggestions.append("Consider checking the expected interfaces of components you're using.")
            for comp in relatedcomponents:
                suggestions.append(f"{comp.name} ({comp.typeof}): {comp.description.split('.')[0]}")

        elif errortype == ErrorType.FRAMEWORKINCOMPATIBLE:
            # For framework incompatibility, suggest alternative frameworks
            frameworks = [c for c in relatedcomponents if c.typeof == "framework"]
            if frameworks:
                names = [c.name for c in frameworks]
                suggestions.append(f"Other available frameworks include: {', '.join(names)}")

        elif errortype == ErrorType.PROPOSITIONINVALID:
            # For invalid propositions, suggest proposition types
            propcomponents = [c for c in relatedcomponents if "Proposition" in c.name]
            if propcomponents:
                names = [c.name for c in propcomponents]
                suggestions.append(f"Available proposition types include: {', '.join(names)}")

        return suggestions

    @classmethod
    def analyzeexception(cls, exception: Exception, errortype: ErrorType) -> ErrorContext:
        """
        Analyze an exception to provide helpful context without prescribing specific solutions.

        Args:
            exception: The exception object to analyze
            errortype: The categorized error type

        Returns:
            ErrorContext with validation context and available components
        """
        try:
            # Extract the traceback as a string for context
            tbstr = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))

            # Extract related framework components
            relatedcomponents = cls.extractframeworkcomponents(exception)

            # Extract validation context
            validationcontext = cls.extractvalidationcontext(exception)

            # Generate suggestions
            suggestions = cls.generatesuggestedcomponents(errortype, relatedcomponents)

            return ErrorContext(
                errortype=errortype,
                message=str(exception),
                exceptiontype=type(exception).__name__,
                traceback=tbstr,
                relatedcomponents=relatedcomponents,
                suggestions=suggestions,
                validationcontext=validationcontext
            )
        except Exception as e:
            log.error(f"Error analyzing exception: {str(e)}")
            # Return a simplified error context when analysis fails
            return ErrorContext(
                errortype=errortype,
                message=str(exception),
                exceptiontype=type(exception).__name__,
                traceback=str(exception),
                suggestions=["Error occurred during exception analysis"]
            )


class ImportErrorAnalyzer:
    """
    Specialized analyzer for import errors.
    Provides information about available modules and components.
    """

    @staticmethod
    def analyze(exception: ImportError) -> dict[str, t.Any]:
        """Analyze an import error to provide helpful context"""
        result = {"errortype": "import_error"}

        # Extract the name that failed to import
        namepattern = r'[\'"]([A-Za-z0-9_\.]+)[\'"]'
        matches = re.findall(namepattern, str(exception))
        if matches:
            imported_name = matches[0]
            result["failed_import"] = imported_name

            # Try to find similar components
            parts = imported_name.split('.')
            similarcomponents = []

            for part in parts:
                if len(part) > 3:  # Avoid very short names
                    similar = frameworkregistry.query(keyword=part)
                    similarcomponents.extend(similar)

            if similarcomponents:
                result["similarcomponents"] = [
                    {
                        "name": comp.name,
                        "type": comp.typeof,
                        "importpath": f"{comp.modulepath}.{comp.classname}"
                    }
                    for comp in similarcomponents[:5]  # Limit to top 5
                ]

        return result


class TypeErrorAnalyzer:
    """
    Specialized analyzer for type errors.
    Provides information about compatible types and interfaces.
    """

    @staticmethod
    def analyze(exception: TypeError) -> dict[str, t.Any]:
        """Analyze a type error to provide helpful context"""
        result = {"errortype": "type_error"}
        errorstr = str(exception)

        # Check for common patterns in type errors
        gotpattern = r'Got:?\s+([A-Za-z0-9_\.]+)'
        expectedpattern = r'[Ee]xpected:?\s+([A-Za-z0-9_\.]+)'

        gotmatch = re.search(gotpattern, errorstr)
        expectedmatch = re.search(expectedpattern, errorstr)

        if gotmatch:
            result["providedtype"] = gotmatch.group(1)

        if expectedmatch:
            result["expectedtype"] = expectedmatch.group(1)

        # Analyze class/interface information
        if hasattr(exception, '__traceback__'):
            tb = traceback.extract_tb(exception.__traceback__)
            if tb:
                lastframe = tb[-1]
                try:
                    # Extract the module and line where the error occurred
                    module_name = lastframe.filename.split('/')[-1].replace('.py', '')
                    linenumber = lastframe.lineno

                    result["location"] = {
                        "module": module_name,
                        "line": linenumber,
                        "function": lastframe.name
                    }
                except Exception:
                    pass

        return result


class ValidationErrorAnalyzer:
    """
    Specialized analyzer for validation errors.
    Provides information about validation constraints and requirements.
    """

    @staticmethod
    def analyze(exception: Exception) -> dict[str, t.Any]:
        """Analyze a validation error to provide helpful context"""
        result = {"errortype": "validation_error"}

        # Extract error message
        errorstr = str(exception)
        result["message"] = errorstr

        # Look for specific constraints in the error message
        constraints = []

        # Check for requirements
        if "require" in errorstr.lower():
            reqpattern = r'requires? ([^\.]+)'
            matches = re.findall(reqpattern, errorstr)
            if matches:
                constraints.extend(matches)

        # Check for invalid values
        if "invalid" in errorstr.lower():
            invalidpattern = r'invalid ([^\.]+)'
            matches = re.findall(invalidpattern, errorstr)
            if matches:
                constraints.extend([f"must not have invalid {m}" for m in matches])

        if constraints:
            result["constraints"] = constraints

        return result


class ErrorContextProvider:
    """
    Provides error context to help guide LLMs in identifying and addressing issues
    without prescribing specific implementations.
    """

    @classmethod
    def getcontext(cls, state: DialogState) -> t.Optional[ErrorContext]:
        """
        Get error context from the current dialog state.

        Args:
            state: The current dialog state containing error information

        Returns:
            ErrorContext with information to guide resolution without prescription
        """
        if not state.error:
            return None

        errortype, exception = state.error
        return ErrorAnalyzer.analyzeexception(exception, errortype)

    @classmethod
    def geterroranalysis(cls, exception: Exception, errortype: ErrorType) -> dict[str, t.Any]:
        """
        Analyze an error based on its type, providing specialized analysis.

        Args:
            exception: Exception object to analyze
            errortype: Categorized error type

        Returns:
            Dictionary with specialized error analysis
        """
        if errortype == ErrorType.IMPORTERROR and isinstance(exception, ImportError):
            return ImportErrorAnalyzer.analyze(exception)

        elif errortype == ErrorType.TYPEERROR and isinstance(exception, TypeError):
            return TypeErrorAnalyzer.analyze(exception)

        elif errortype == ErrorType.VALIDATIONFAILED or errortype == ErrorType.PROPOSITIONINVALID:
            return ValidationErrorAnalyzer.analyze(exception)

        # Default analysis
        return {
            "errortype": errortype.name.lower(),
            "message": str(exception),
            "exceptiontype": type(exception).__name__
        }
