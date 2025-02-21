# ~/formalities/src/formalities/utils/formatting.py
import black
from loguru import logger as log

INDENT = '   '

def formatcode(code: str) -> str:
    """
    Format code string using black.

    Args:
        code: Python code string to format
    Returns:
        Formatted code string
    Raises:
        ValueError: If code cannot be parsed/formatted
    """
    def preprocess() -> str:
        lines = code.strip().split('\n')
        cleaned = []
        infunc = False
        for line in lines:
            if (stripped:=line.strip()).startswith('def'):
                infunc = True
                cleaned.append(line)
            elif infunc and stripped:
                cleaned.append(INDENT + stripped)
            else:
                cleaned.append(line)
        return '\n'.join(cleaned)

    try:
        return black.format_str(preprocess(), mode=black.Mode())
    except Exception as e:
        log.error(f"formatcode | black formatting exception | {str(e)}")
        raise ValueError(f"Invalid Code Structure: {str(e)}")
