# ~/formalities/src/formalities/fall/core/types/language/numerical.py
from __future__ import annotations
import re, enum, typing as t
from dataclasses import dataclass, field
from formalities.fall.core.types.language.base import (
    Word, Statement
)
from formalities.fall.core.types.language.common import (
    WordType, WordFunction, RelationshipType, StatementType,
    POS, KNOWN, PATTERNS, CheckFunctions
)
from loguru import logger as log

class NumericalOperationType(enum.Enum):
    """Types of numerical operations that can be validated."""
    COUNTING = enum.auto()
    ADDITION = enum.auto()
    SUBTRACTION = enum.auto()
    MULTIPLICATION = enum.auto()
    DIVISION = enum.auto()
    COMPARISON = enum.auto()
    MEASUREMENT = enum.auto()
    UNKNOWN = enum.auto()

class NumericalValidator:
    """
    Validator for numerical statements.

    This validator builds upon existing statement extraction in base.py
    providing enhanced validation and verification capabilities
    """
    @classmethod
    def _enhancecounting(cls, statement: Statement, structure: dict) -> dict:
        """
        Enhance counting structure with details, focusing on verification.
        """
        log.info(f"Enhancing counting for: '{statement.content}'")
        log.debug(f"Initial counting structure: {structure}")

        # Use subject as container if available
        if statement.subjects:
            subject = statement.subjects[0].content
            log.debug(f"Found subject: {subject}")
            structure['container'] = subject
            log.debug(f"Set container from subject: {subject}")

        # Try to extract countable - using multiple patterns to be robust
        if 'countable' not in structure or structure['countable'] is None:
            # First try the specific pattern for "has N X's" or "are N X's"
            for pattern in [
                r"has\s+\d+\s+(\w)'s",  # matches "has 4 s's"
                r"are\s+\d+\s+(\w)'s",  # matches "are 3 a's"
                r"contains\s+\d+\s+(\w)'s",  # matches "contains 2 b's"
            ]:
                match = re.search(pattern, statement.content.lower())
                if match:
                    countable = match.group(1)
                    structure['countable'] = countable
                    log.debug(f"Extracted countable using pattern '{pattern}': '{countable}'")
                    break

            # If still not found, try more general patterns
            if 'countable' not in structure or structure['countable'] is None:
                for pattern in [
                    r"(\w)'s\b",  # matches "r's" at word boundary
                    r"(\w)'s",    # matches any "X's"
                    r"(\w) in",   # matches "X in"
                ]:
                    match = re.search(pattern, statement.content.lower())
                    if match:
                        countable = match.group(1)
                        structure['countable'] = countable
                        log.debug(f"Extracted countable using fallback pattern '{pattern}': '{countable}'")
                        break

        # Now process the structure if we have both container and countable
        if ('countable' in structure and structure['countable'] and
            'container' in structure and structure['container']):

            countable = structure['countable']
            container = structure['container']
            log.debug(f"Processing with countable '{countable}' and container '{container}'")

            # Determine if this is character counting
            structure['ischaractercounting'] = (len(countable) == 1)
            log.debug(f"Is character counting: {structure['ischaractercounting']}")

            # Calculate the actual count
            if 'actualcount' not in structure and structure.get('ischaractercounting', False):
                count = container.lower().count(countable.lower())
                structure['actualcount'] = count
                log.debug(f"Calculated actual count of '{countable}' in '{container}': {count}")

                # Print characters for debugging WITHOUT any special casing
                if log.level('DEBUG').enabled:
                    for i, char in enumerate(container.lower()):
                        log.debug(f"  Char {i}: '{char}' {'(match)' if char == countable.lower() else ''}")

            # Extract claimed count from numbers in structure
            if 'claimedcount' not in structure:
                for num in structure.get('numbers', []):
                    if num.get('function') in ['RESULT', 'PREDICATEADJECTIVE']:
                        structure['claimedcount'] = num.get('value')
                        log.debug(f"Extracted claimed count: {structure['claimedcount']}")
                        break

            # Determine if the count is valid
            if 'actualcount' in structure and 'claimedcount' in structure:
                structure['isvalid'] = (structure['actualcount'] == structure['claimedcount'])
                log.debug(f"Count validity: {structure['isvalid']} (actual: {structure['actualcount']}, claimed: {structure['claimedcount']})")

        log.debug(f"Final counting structure: {structure}")
        return structure

    @classmethod
    def _validatearithmetic(cls, statement: Statement, structure: dict) -> t.Tuple[bool, str]:
        components = structure.get('components', {})
        result = structure.get('result')

        if ('operands' not in components) or ('operator' not in components):
            return (False, "Incomplete arithmetic statement")

        operands = components.get('operands', [])
        operator = components.get('operator')
        expectedresult = components.get('expectedresult')

        if (len(operands) < 2) or (expectedresult is None) or (result is None):
            return (False, "Insufficient information for validation")

        if (expectedresult != result):
            opsymbol = "+"
            if operator in ['minus', 'subtract', 'subtracted from']:
                opsymbol = "-"
            elif operator in ['times', 'multiply', 'multiplied by']:
                opsymbol = "×"
            elif operator in ['divide', 'divided by']:
                opsymbol = "÷"

            return (False, f"Incorrect: {operands[0]} {opsymbol} {operands[1]} = {expectedresult}, not {result}")

        return (True, f"Correct: The result is {result}")

    @classmethod
    def _validatecomparison(cls, statement: Statement, structure: dict) -> t.Tuple[bool, str]:
        components = structure.get('components', {})

        if ('values' not in components) or ('comparison' not in components):
            return (False, "Incomplete comparison statement")

        values = components.get('values', [])
        comparison = components.get('comparison')
        result = components.get('result', False)

        if len(values) < 2:
            return (False, "Need at least two values to compare")

        left = values[0]
        right = values[1]

        actualresult = False
        if comparison in ['greater than', 'more than']:
            actualresult = left > right
        elif comparison in ['less than', 'fewer than']:
            actualresult = left < right
        elif comparison in ['equal to', 'equals']:
            actualresult = left == right
        elif comparison == 'at least':
            actualresult = left >= right
        elif comparison == 'at most':
            actualresult = left <= right

        if actualresult == result:
            return (True, f"Correct: {left} is {comparison} {right}")
        else:
            return (False, f"Incorrect: {left} is NOT {comparison} {right}")


    @classmethod
    def _getoperatorsymbol(cls, operator: str) -> str:
        """Get a display symbol for an operator."""
        if operator in ['plus', 'add', 'added to']:
            return "+"
        elif operator in ['minus', 'subtract', 'subtracted from']:
            return "-"
        elif operator in ['times', 'multiply', 'multiplied by']:
            return "×"
        elif operator in ['divide', 'divided by']:
            return "÷"
        return operator

    @classmethod
    def _generatesuccessmessage(cls, structure: dict) -> str:
        """Generate a success message based on available structure information."""
        # Determine what type of statement we're dealing with
        if 'countable' in structure and 'container' in structure and 'actualcount' in structure:
            # Counting statement
            return f"Correct: There are {structure['actualcount']} '{structure['countable']}'s in '{structure['container']}'"
        elif 'components' in structure and 'result' in structure:
            components = structure['components']
            if 'operands' in components and 'operator' in components:
                # Arithmetic statement
                return f"Correct: The result is {structure['result']}"
            elif 'values' in components and 'comparison' in components:
                # Comparison statement
                values = components['values']
                if len(values) >= 2:
                    return f"Correct: {values[0]} is {components['comparison']} {values[1]}"

        # Generic success
        return "The numerical statement is valid"

    @classmethod
    def _generatefailuremessage(cls, structure: dict) -> str:
        """Generate a failure message based on available structure information."""
        # Determine what type of statement we're dealing with
        if 'countable' in structure and 'container' in structure and 'actualcount' in structure and 'claimedcount' in structure:
            # Counting statement
            return f"Incorrect: There are {structure['actualcount']} '{structure['countable']}'s in '{structure['container']}', not {structure['claimedcount']}"
        elif 'components' in structure and 'result' in structure:
            components = structure['components']
            if 'operands' in components and 'operator' in components and 'expectedresult' in components:
                # Arithmetic statement
                opsymbol = cls._getoperatorsymbol(components['operator'])
                operands = components['operands']
                if len(operands) >= 2:
                    return f"Incorrect: {operands[0]} {opsymbol} {operands[1]} = {components['expectedresult']}, not {structure['result']}"
            elif 'values' in components and 'comparison' in components:
                # Comparison statement
                values = components['values']
                if len(values) >= 2:
                    return f"Incorrect: {values[0]} is NOT {components['comparison']} {values[1]}"

        # Generic failure
        return "The numerical statement is invalid"

    @classmethod
    def Validate(cls, statement: Statement) -> t.Tuple[bool, str]:
        """
        Validate a numerical statement by focusing on verification of the claim itself.
        """
        log.info(f"Validating numerical statement: '{statement.content}'")

        if statement.type != StatementType.NUMERICAL:
            return (False, "Not a numerical statement")

        # Always use enhanced structure for validation to ensure proper operation type detection
        structure = NumericalStructureExtractor.extract(statement)
        log.debug(f"Structure for validation: {structure}")

        # Determine operation type
        optype = structure.get('operationtype')
        log.debug(f"Operation type determined: {optype}")

        # Check for direct validity indicator
        if 'isvalid' in structure:
            log.debug(f"Structure contains validity determination: {structure['isvalid']}")
            valid = structure['isvalid']
            if valid:
                return (True, cls._generatesuccessmessage(structure))
            else:
                return (False, cls._generatefailuremessage(structure))

        # Validate based on operation type
        if optype == 'arithmetic':
            components = structure.get('components', {})
            operands = components.get('operands', [])
            operator = components.get('operator')
            result = structure.get('result')

            log.debug(f"Arithmetic validation: operands={operands}, operator={operator}, result={result}")

            if len(operands) >= 2 and operator and result is not None:
                # Calculate expected result
                expected = None
                if operator in ['plus', 'add', 'added to']:
                    expected = operands[0] + operands[1]
                elif operator in ['minus', 'subtract', 'subtracted from']:
                    expected = operands[0] - operands[1]
                elif operator in ['times', 'multiply', 'multiplied by']:
                    expected = operands[0] * operands[1]
                # Add specific handling for "divided by"
                elif operator in ['divide', 'divided by', 'divided']:
                    if operands[1] != 0:
                        expected = operands[0] / operands[1]
                        # Convert to int if it's a whole number
                        if expected == int(expected):
                            expected = int(expected)

                if expected is not None:
                    log.debug(f"Calculated expected result: {expected}")
                    isvalid = (expected == result)
                    log.debug(f"Arithmetic validation result: {isvalid}")

                    if isvalid:
                        return (True, f"Correct: {operands[0]} {cls._getoperatorsymbol(operator)} {operands[1]} = {result}")
                    else:
                        opsymbol = cls._getoperatorsymbol(operator)
                        return (False, f"Incorrect: {operands[0]} {opsymbol} {operands[1]} = {expected}, not {result}")

        # Counting validation
        elif optype == 'counting':
            countable = structure.get('countable')
            container = structure.get('container')

            if countable and container:
                # Calculate actual count
                actual = structure.get('actualcount')
                if actual is None:
                    actual = container.lower().count(countable.lower())
                    structure['actualcount'] = actual
                    log.debug(f"Calculated actual count: {actual}")

                # Get claimed count
                claimed = structure.get('claimedcount')
                if claimed is None:
                    for num in structure.get('numbers', []):
                        if num.get('function') in ['RESULT', 'PREDICATEADJECTIVE']:
                            claimed = num.get('value')
                            log.debug(f"Found claimed count: {claimed}")
                            break

                if actual is not None and claimed is not None:
                    isvalid = (actual == claimed)
                    log.debug(f"Counting validation result: {isvalid}")

                    if isvalid:
                        return (True, f"Correct: There are {actual} '{countable}'s in '{container}'")
                    else:
                        return (False, f"Incorrect: There are {actual} '{countable}'s in '{container}', not {claimed}")

        # Comparison validation
        elif optype == 'comparison':
            components = structure.get('components', {})
            values = components.get('values', [])
            comparison = components.get('comparison')

            if len(values) >= 2 and comparison:
                left, right = values[0], values[1]
                actualresult = False

                # Determine if comparison is true
                if comparison in ['greater than', 'more than']:
                    actualresult = left > right
                elif comparison in ['less than', 'fewer than']:
                    actualresult = left < right
                elif comparison in ['equal to', 'equals']:
                    actualresult = left == right
                elif comparison == 'at least':
                    actualresult = left >= right
                elif comparison == 'at most':
                    actualresult = left <= right

                # The statement is valid if the comparison is factually true
                if actualresult:
                    return (True, f"Correct: {left} is {comparison} {right}")
                else:
                    return (False, f"Incorrect: {left} is NOT {comparison} {right}")

        # If we can't validate with the enhanced structure, report inability to verify
        return (False, "Unable to verify the numerical statement with available information")


class NumericalStructureExtractor:
    """
    Enhanced extraction utilities for numerical statements.

    This class provides more specialized extraction methods beyond
    what's available in the base Statement class.
    """

    @classmethod
    def extract(cls, statement: Statement) -> dict:
        """
        Extract numerical structure from a statement.
        This is the main entry point for numerical extraction.
        """
        if statement.type != StatementType.NUMERICAL:
            log.debug(f"Not a numerical statement: {statement.content}")
            return {}

        # Get base structure from statement
        structure = statement.numericalstructure
        log.info(f"Starting numerical extraction for: '{statement.content}'")
        log.debug(f"Initial structure from statement: {structure}")

        # Ensure we have a valid structure
        if not structure:
            structure = cls._extractfromscratch(statement)

        # Determine operation type based on relationships and content
        content = statement.content.lower()

        # Check relationships first
        if RelationshipType.ARITHMETIC in statement._relationships:
            structure['operationtype'] = 'arithmetic'
        elif RelationshipType.COUNTING in statement._relationships:
            structure['operationtype'] = 'counting'
        elif RelationshipType.COMPARISON in statement._relationships:
            structure['operationtype'] = 'comparison'

        # If not determined by relationships, check content patterns
        if 'operationtype' not in structure or not structure['operationtype']:
            # Check for arithmetic keywords
            arithmetic_terms = ['plus', 'minus', 'times', 'multiply', 'divide', 'add', 'subtract']
            if any(term in content for term in arithmetic_terms):
                structure['operationtype'] = 'arithmetic'
            # Check for counting patterns
            elif any(pattern in content for pattern in ["in", "has", "contain", "there are"]):
                structure['operationtype'] = 'counting'
            # Check for comparison patterns
            elif any(pattern in content for pattern in ["greater than", "less than", "equal to"]):
                structure['operationtype'] = 'comparison'

        # Enhance with operation-specific extraction
        if structure.get('operationtype') == 'counting':
            log.info(f"Enhancing counting structure for: '{statement.content}'")
            structure = cls._enhancecounting(statement, structure)
        elif structure.get('operationtype') == 'arithmetic':
            log.info(f"Enhancing arithmetic structure for: '{statement.content}'")
            structure = cls._enhancearithmetic(statement, structure)
        elif structure.get('operationtype') == 'comparison':
            log.info(f"Enhancing comparison structure for: '{statement.content}'")
            structure = cls._enhancecomparison(statement, structure)

        # Add convenience access to validation
        structure['validate'] = lambda: NumericalValidator.Validate(statement)
        log.debug(f"Final structure: {structure}")
        return structure

    @classmethod
    def _extractfromscratch(cls, statement: Statement) -> dict:
        """Extract numerical structure when none is available from the statement."""
        structure = {
            'operationtype': None,
            'numbers': [],
            'components': {}
        }

        # Extract numbers
        for word in statement._words:
            if word.type == WordType.NUMBER:
                try:
                    value = None
                    if word.content.lower() in KNOWN.NUMBERWORDS:
                        value = list(KNOWN.NUMBERWORDS).index(word.content.lower())
                        log.debug(f"Extracted number word: '{word.content}' = {value}")
                    else:
                        value = int(word.content)
                        log.debug(f"Extracted numeric digit: '{word.content}' = {value}")

                    structure['numbers'].append({
                        'word': word.content,
                        'value': value,
                        'function': word.function.name if word.function else None
                    })
                except (ValueError, TypeError):
                    log.warning(f"Failed to extract number from '{word.content}': {str(e)}")

        # Determine operation type
        if any(term in statement.content.lower() for term in ['in', 'contain', 'has']):
            structure['operationtype'] = 'counting'
            log.debug(f"Detected counting operation type")
        elif any(op in statement.content.lower() for op in KNOWN.ARITHMETICOPERATORS):
            structure['operationtype'] = 'arithmetic'
            log.debug(f"Detected arithmetic operation type")
        elif any(term in statement.content.lower() for term in KNOWN.COMPARANS):
            structure['operationtype'] = 'comparison'
            log.debug(f"Detected comparison operation type")
        # Extract container and countable for counting operations
        ## MORE COMPREHENSIVE SOLUTION NEEDED FOR FUTURE ##
        if structure.get('operationtype') == 'counting':
            # Look for patterns like "in X" to find container
            match = re.search(r"in\s+(\w+)", statement.content.lower())
            if match:
                structure['container'] = match.group(1)
                log.debug(f"Extracted container: '{structure['container']}'")

            # Look for countable pattern
            match = re.search(r"(\w)'s", statement.content.lower())
            if match:
                structure['countable'] = match.group(1)
                log.debug(f"Extracted countable: '{structure['countable']}'")

        return structure

    @classmethod
    def _enhancecounting(cls, statement: Statement, structure: dict) -> dict:
        """
        Enhance counting structure with additional details.

        This method prioritizes verification over pattern-matching by:
        1. Extracting necessary components without prescriptive assumptions
        2. Approaching the problem from multiple angles
        3. Focusing on validation rather than structure enforcement

        Examples:
        - "There are 2 r's in strawberry"
        - "Strawberry has 2 r's"
        - "Mississippi has 4 s's"
        """
        log.info(f"Enhancing counting for: '{statement.content}'")
        log.debug(f"Initial counting structure: {structure}")

        content = statement.content.lower()

        # Try extracting container through multiple approaches
        # 1. Check if structure already has container
        # 2. Try subject-based extraction (for "X has N y's" pattern)
        # 3. Try prepositional phrase extraction (for "N x's in Y" pattern)

        if 'container' not in structure or not structure.get('container'):
            # Check subjects first (for "X has N y's")
            if statement.subjects:
                structure['container'] = statement.subjects[0].content
                log.debug(f"Extracted container from subject: {structure['container']}")

            # Then try prepositional phrase (for "N x's in Y")
            elif "in " in content:
                prep_match = re.search(r"in\s+(\w+)", content)
                if prep_match:
                    structure['container'] = prep_match.group(1)
                    log.debug(f"Extracted container from prepositional phrase: {structure['container']}")

        # Try extracting countable through multiple approaches
        # 1. Check if structure already has countable
        # 2. Try pattern matching for the quoted character

        if 'countable' not in structure or not structure.get('countable'):
            # Try different patterns for finding the countable character
            for pattern in [
                r"(\w)'s\s+in",         # "r's in" pattern
                r"has\s+\d+\s+(\w)'s",  # "has N x's" pattern
                r"are\s+\d+\s+(\w)'s",  # "are N x's" pattern
                r"(\w)'s",              # generic "x's" pattern
            ]:
                match = re.search(pattern, content)
                if match:
                    structure['countable'] = match.group(1)
                    log.debug(f"Extracted countable using pattern: {pattern} -> '{structure['countable']}'")
                    break

        # If we have both container and countable, perform the counting verification
        if structure.get('container') and structure.get('countable'):
            container = structure['container']
            countable = structure['countable']
            log.debug(f"Working with container: '{container}' and countable: '{countable}'")

            # Perform the count - character counting for single-character countables
            ischarcounting = len(countable) == 1
            structure['ischaractercounting'] = ischarcounting

            if ischarcounting and 'actualcount' not in structure:
                actualcount = container.lower().count(countable.lower())
                structure['actualcount'] = actualcount
                log.debug(f"Calculated count: container='{container}', countable='{countable}', count={actualcount}")

                # Debug char-by-char for specific troublesome patterns
                #if log.level('DEBUG').enabled:
                log.debug(f"Character-by-character analysis of '{container}':")
                for i, char in enumerate(container.lower()):
                    matchstatus = "(match)" if char == countable.lower() else ""
                    log.debug(f"  Pos {i}: '{char}' {matchstatus}")

            # Extract claimed count from numerical components
            if 'claimedcount' not in structure:
                # First check numbers with explicit functions
                for num in structure.get('numbers', []):
                    func = num.get('function')
                    if func in ['RESULT', 'PREDICATEADJECTIVE']:
                        structure['claimedcount'] = num.get('value')
                        log.debug(f"Found claimed count from {func}: {structure['claimedcount']}")
                        break

                # If still not found, try any number in the statement
                if 'claimedcount' not in structure and structure.get('numbers'):
                    # Assume the first number is the claimed count
                    firstnum = structure['numbers'][0]
                    structure['claimedcount'] = firstnum.get('value')
                    log.debug(f"Using first number as claimed count: {structure['claimedcount']}")

            # Validation - compare actual vs claimed count
            if 'actualcount' in structure and 'claimedcount' in structure:
                structure['isvalid'] = (structure['actualcount'] == structure['claimedcount'])
                validationmsg = "valid" if structure['isvalid'] else "invalid"
                log.debug(f"Count validation result: {validationmsg} (actual={structure['actualcount']}, claimed={structure['claimedcount']})")

        # If we have only one of container or countable, provide informative feedback
        elif structure.get('container') and not structure.get('countable'):
            log.debug(f"Found container '{structure['container']}' but missing countable element")
        elif structure.get('countable') and not structure.get('container'):
            log.debug(f"Found countable '{structure['countable']}' but missing container element")

        log.debug(f"Final counting structure: {structure}")
        return structure

    @classmethod
    def _enhancearithmetic(cls, statement: Statement, structure: dict) -> dict:
        """
        Enhance arithmetic structure with additional details.

        This method extracts operands, operators, and results from arithmetic statements
        and verifies their logical consistency.

        Examples:
        - "2 plus 2 equals 4"
        - "5 minus 3 equals 2"
        - "10 divided by 2 equals 5"
        """
        log.info(f"Enhancing arithmetic for: '{statement.content}'")
        log.debug(f"Initial arithmetic structure: {structure}")

        content = statement.content.lower()
        components = structure.get('components', {})

        # Extract operands
        operands = []
        # First try function-tagged operands
        for word in statement._words:
            if word.function == WordFunction.OPERAND:
                try:
                    if word.content.lower() in KNOWN.NUMBERWORDS:
                        value = list(KNOWN.NUMBERWORDS).index(word.content.lower())
                    else:
                        value = int(word.content)
                    operands.append(value)
                    log.debug(f"Found operand from function: {value}")
                except (ValueError, TypeError) as e:
                    log.debug(f"Error parsing operand '{word.content}': {str(e)}")

        # If operands not found by function, try pattern matching
        if not operands:
            # Extract numbers from structure
            numbers = []
            for num in structure.get('numbers', []):
                if num.get('value') is not None:
                    numbers.append(num.get('value'))

            # For simple arithmetic, first two numbers are likely operands
            if len(numbers) >= 2:
                operands = numbers[:2]
                log.debug(f"Extracted operands from position: {operands}")

        components['operands'] = operands
        log.debug(f"Final operands: {operands}")

        # Extract operator
        operator = None
        # First try function-tagged operator
        for word in statement._words:
            if word.function == WordFunction.OPERATOR:
                operator = word.content.lower()
                log.debug(f"Found operator from function: {operator}")
                break

        # If not found, try content matching
        if not operator:
            # Check for "divided by" in the content
            if "divided by" in content:
                operator = "divided by"
                log.debug(f"Found operator from content: {operator}")
            else:
                # Check for other operators
                for op in KNOWN.ARITHMETICOPERATORS:
                    if op in content:
                        operator = op
                        log.debug(f"Found operator from content: {operator}")
                        break

        components['operator'] = operator

        # Extract result - usually after "equals" or as the last number
        result = None
        # First try function-tagged result
        for word in statement._words:
            if word.function == WordFunction.RESULT:
                try:
                    if word.content.lower() in KNOWN.NUMBERWORDS:
                        result = list(KNOWN.NUMBERWORDS).index(word.content.lower())
                    else:
                        result = int(word.content)
                    log.debug(f"Found result from function: {result}")
                    break
                except (ValueError, TypeError) as e:
                    log.debug(f"Error parsing result '{word.content}': {str(e)}")

        # If not found and we have numbers, assume the last one is the result
        if result is None and structure.get('numbers') and len(structure['numbers']) > 2:
            result = structure['numbers'][-1].get('value')
            log.debug(f"Inferred result from position: {result}")

        structure['result'] = result

        # Calculate expected result
        expected = None
        if len(operands) >= 2 and operator:
            if operator in ['plus', 'add', 'added to']:
                expected = operands[0] + operands[1]
            elif operator in ['minus', 'subtract', 'subtracted from']:
                expected = operands[0] - operands[1]
            elif operator in ['times', 'multiply', 'multiplied by']:
                expected = operands[0] * operands[1]
            elif operator in ['divide', 'divided by'] and operands[1] != 0:
                expected = operands[0] / operands[1]
                # Convert to int if it's a whole number
                if expected == int(expected):
                    expected = int(expected)

            if expected is not None:
                components['expectedresult'] = expected
                log.debug(f"Calculated expected result: {expected}")

        # Validate the arithmetic operation
        if 'expectedresult' in components and result is not None:
            structure['isvalid'] = (components['expectedresult'] == result)
            log.debug(f"Arithmetic validation: {structure['isvalid']} (expected={components['expectedresult']}, actual={result})")

        structure['components'] = components
        log.debug(f"Final arithmetic structure: {structure}")
        return structure

    @classmethod
    def _enhancecomparison(cls, statement: Statement, structure: dict) -> dict:
        """
        Enhance comparison structure with additional details.

        Examples:
        - "5 is greater than 3"
        - "10 is equal to 10"
        """
        components = structure.get('components', {})

        # Extract values to compare
        if 'values' not in components:
            values = []
            for num in structure.get('numbers', []):
                if num.get('value') is not None:
                    values.append(num.get('value'))
            components['values'] = values

        # Extract comparison operator
        if 'comparison' not in components:
            for op in KNOWN.COMPARANS:
                if op in statement.content.lower():
                    components['comparison'] = op
                    break

        # Calculate result of comparison
        if 'result' not in components and 'values' in components and 'comparison' in components:
            values = components['values']
            comparison = components['comparison']

            if len(values) >= 2:
                left = values[0]
                right = values[1]

                if comparison in ['greater than', 'more than']:
                    components['result'] = left > right
                elif comparison in ['less than', 'fewer than']:
                    components['result'] = left < right
                elif comparison in ['equal to', 'equals']:
                    components['result'] = left == right
                elif comparison == 'at least':
                    components['result'] = left >= right
                elif comparison == 'at most':
                    components['result'] = left <= right

        # Determine if the comparison is valid
        if 'result' in components:
            structure['isvalid'] = components['result']

        structure['components'] = components
        return structure


class NumericalStatement(Statement):
    """
    Specialized statement class for numerical statements.

    This extends the base Statement class with numerical-specific functionality.
    """
    def __init__(self, content: str):
        super().__init__(content)
        # Initialize properties
        self._operationtype = None
        self._operands = []
        self._operator = None
        self._result = None  # Use _result (instance variable) not result (property)
        self._comparison = None
        self._enhancedstructure = None

        # Extract numerical components if appropriate
        if self.type == StatementType.NUMERICAL:
            self._extractnumericalcomponents()

    def _extractnumericalcomponents(self) -> None:
        """Extract numerical components based on statement type."""
        # Get numerical structure
        if not self._numericalstructure:
            self._numericalstructure = self._extractnumericalstructure()

        # Determine operation type from relationships or structure
        if RelationshipType.COUNTING in self._relationships:
            self._operationtype = 'counting'
        elif RelationshipType.ARITHMETIC in self._relationships:
            self._operationtype = 'arithmetic'
        elif RelationshipType.COMPARISON in self._relationships:
            self._operationtype = 'comparison'

        # If we have a structure, use its operation type
        if self._numericalstructure and 'operationtype' in self._numericalstructure:
            self._operationtype = self._numericalstructure['operationtype']

        # Extract operands
        self._operands = [word.content for word in self._words if word.function == WordFunction.OPERAND]

        # Extract operator
        operators = [word.content for word in self._words if word.function == WordFunction.OPERATOR]
        self._operator = operators[0] if operators else None

        # Extract result
        results = [word.content for word in self._words if word.function == WordFunction.RESULT]
        self._result = results[0] if results else None

    @property
    def operationtype(self) -> t.Optional[str]:
        """Get the type of numerical operation."""
        if self._operationtype is None:
            # Determine type from relationships and structure
            if RelationshipType.COUNTING in self._relationships:
                self._operationtype = 'counting'
            elif RelationshipType.ARITHMETIC in self._relationships:
                self._operationtype = 'arithmetic'
            elif RelationshipType.COMPARISON in self._relationships:
                self._operationtype = 'comparison'

            # Also check numerical structure
            if self._numericalstructure and 'operationtype' in self._numericalstructure:
                self._operationtype = self._numericalstructure['operationtype']

        return self._operationtype

    @property
    def operands(self) -> t.List[str]:
        """Get the operands in the statement."""
        if not self._operands:
            self._operands = [word.content for word in self._words if word.function == WordFunction.OPERAND]
        return self._operands

    @property
    def operandvalues(self) -> t.List[int]:
        """Get the operand values as integers."""
        result = []
        for operand in self.operands:
            try:
                if operand.lower() in KNOWN.NUMBERWORDS:
                    result.append(list(KNOWN.NUMBERWORDS).index(operand.lower()))
                else:
                    result.append(int(operand))
            except (ValueError, TypeError):
                pass
        return result

    @property
    def operator(self) -> t.Optional[str]:
        """Get the operator in the statement."""
        if not self._operator:
            operators = [word.content for word in self._words if word.function == WordFunction.OPERATOR]
            self._operator = operators[0] if operators else None
        return self._operator

    @property
    def result(self) -> t.Optional[str]:
        """Get the result string in the statement."""
        if not self._result:
            results = [word.content for word in self._words if word.function == WordFunction.RESULT]
            self._result = results[0] if results else None
        return self._result

    @property
    def resultvalue(self) -> t.Optional[int]:
        """Get the result value as an integer."""
        if not self.result:
            return None

        try:
            if self.result.lower() in KNOWN.NUMBERWORDS:
                return list(KNOWN.NUMBERWORDS).index(self.result.lower())
            else:
                return int(self.result)
        except (ValueError, TypeError):
            return None

    @property
    def enhancedstructure(self) -> dict:
        """Get enhanced numerical structure with detailed extraction."""
        if not self._enhancedstructure:
            self._enhancedstructure = NumericalStructureExtractor.extract(self)
        return self._enhancedstructure

    def validate(self) -> t.Tuple[bool, str]:
        """Validate the numerical statement."""
        return NumericalValidator.Validate(self)

    @classmethod
    def FromStatement(cls, statement: Statement) -> 'NumericalStatement':
        """Create a NumericalStatement from a regular Statement."""
        if statement.type != StatementType.NUMERICAL:
            raise ValueError("Cannot convert non-numerical statement to NumericalStatement")

        result = cls(statement.content)
        # Copy over any already processed data
        result._type = statement._type
        result._words = statement._words
        result._relationships = statement._relationships
        result._numericalstructure = statement._numericalstructure

        # Ensure numerical components are extracted
        result._extractnumericalcomponents()

        return result
