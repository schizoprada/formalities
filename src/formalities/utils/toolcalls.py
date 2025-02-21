# ~/formalities/src/formalities/utils/toolcalls.py
from __future__ import annotations
import inspect, typing as t
from dataclasses import dataclass
from formalities.utils.typesys import typehandler
from formalities.utils.discovery import frameworkregistry, ComponentInfo
from formalities.utils.formatting import formatcode
from formalities.validation.base import ValidationContext, Validator
from formalities.core.types.propositions import Proposition
from loguru import logger as log

@dataclass
class ToolCallRequest:
    """Represents a tool call request from an LLM"""
    tool: str
    query: dict[str, t.Any]

@dataclass
class ToolCallResponse:
    success: bool
    data: t.Optional[dict[str, t.Any]] = None
    error: t.Optional[str] = None


class ToolCallHandler:

    def __init__(self):
        self._registry = frameworkregistry

    def _getimports(self, components: list[ComponentInfo]) -> list[str]:
        imports = [f"from {comp.modulepath} import {comp.classname}" for comp in components]
        return list(set(imports))

    def _matchmaker(self, query: dict) -> ToolCallResponse:
        try:
            task = query.get("task")
            needs = query.get("needs", [])

            components = []

            if (frameworks:=self._registry.query(comptype="framework")):
                components.extend(frameworks)

            for need in needs:
                matches = self._registry.query(keyword=need)
                components.extend(matches)

            return ToolCallResponse(
                success=True,
                data={
                    "available": [
                        {
                            "name": comp.name,
                            "type": comp.typeof,
                            "description": comp.description,
                            "modulepath": f"{comp.modulepath}.{comp.classname}"
                        }
                        for comp in components
                    ],
                    "imports": self._getimports(components)
                }
            )
        except Exception as e:
            log.error(f"ToolCallHandler._matchmaker | exception | {str(e)}")
            return ToolCallResponse(
                success=False,
                error=f"Matchmaker Error: {str(e)}"
            )

    def _methodbuilder(self, query: dict) -> ToolCallResponse:
        """Enhanced method builder with pre-execution validation"""

        def validateparams() -> tuple[bool, (str | None)]:
            """validate input parameters"""
            if (errors := typehandler.validateparams(query,
                {
                    "code": str,
                    "frameworks": list,
                    "validators": list
                }
            )):
                return False, f"Parameter validation failed: {'; '.join(errors)}"
            return True, None

        def compilecode(code: str) -> tuple[bool, (dict | str)]:
            """Compile code and return namespace"""
            namespace = {}
            try:
                exec(code, namespace)
                return True, namespace
            except Exception as e:
                return False, f"Code Compilation Error: {str(e)}"

        def getmain(namespace: dict) -> tuple[bool, (t.Callable | str)]:
            """Get main function from namespace"""
            if (mainfunc := next((
                obj for name, obj in namespace.items()
                if inspect.isfunction(obj)
            ), None)):
                return True, mainfunc
            return False, "No function found in the provided code"

        def validateargs(func: t.Callable) -> tuple[bool, (str | None)]:
            """Validate function arguments"""
            sig = inspect.signature(func)
            required = {
                name: param.annotation
                for name, param in sig.parameters.items()
                if param.default == param.empty
            }
            if (missing := [name for name in required if name not in query.get('args', {})]):
                return False, f"Missing required arguments: {', '.join(missing)}"
            return True, None

        def loadcomponents() -> tuple[bool, (dict | str)]:
            """Load frameworks and validators"""
            loaded = {"frameworks": [], "validators": []}
            for framework in query.get("frameworks", []):
                if (fclass := self._registry.getcomp(framework)):
                    loaded["frameworks"].append(fclass())
                else:
                    return False, f"Framework not found: {framework}"
            for validator in query.get("validators", []):
                if (vclass := self._registry.getcomp(validator)):
                    loaded["validators"].append(vclass())
                else:
                    return False, f"Validator not found: {validator}"
            if not loaded["frameworks"]:
                return False, "At least one framework is required for validation"
            return True, loaded

        def execute(func: t.Callable, args: dict) -> tuple[bool, t.Any]:
            """Execute function with arguments"""
            try:
                result = func(**args)
                return True, result
            except Exception as e:
                return False, f"Function Execution Error: {str(e)}"

        def convert(result: t.Any) -> tuple[bool, (Proposition | str)]:
            """Convert result to proposition"""
            if isinstance(result, Proposition):
                return True, result
            conversion = typehandler.toprop(result, "result")
            if not conversion.success:
                return False, f"Failed to convert result: {conversion.error}"
            return True, conversion.value

        def validateresult(result: Proposition, components: dict) -> tuple[bool, (dict | str)]:
            """Validate result using components"""
            primaryfw = components["frameworks"][0]
            context = ValidationContext(
                framework=primaryfw,
                options=query.get("args", {})
            )
            validator = Validator(primaryfw)

            for fw in components["frameworks"][1:]:
                validator.addstrategy(fw)
                log.debug(f"ToolCallHandler._methodbuilder | added framework strategy: {fw.__class__.__name__}")

            for v in components["validators"]:
                validator.addstrategy(v)
                log.debug(f"ToolCallHandler._methodbuilder | added validator strategy: {v.__class__.__name__}")

            log.debug(f"ToolCallHandler._methodbuilder | validator strategies: {[s.__class__.__name__ for s in validator._strategies]}")
            validated, valctx = validator.validate(result)
            log.debug(f"ToolCallHandler._methodbuilder | validation result: {validated}")

            if not validated.isvalid:
                return False, "; ".join(validated.errors)
            return True, {
                "result": result,
                "validation": {
                    "context": valctx,
                    "history": valctx.history
                },
                "errors": validated.errors
            }

        try:
            # Extract and validate initial parameters
            code, frameworks, validators, args = (
                query.get(key, default) for key, default in (
                    ("code", None),
                    ("frameworks", []),
                    ("validators", []),
                    ("args", {})
                )
            )

            if not code:
                return ToolCallResponse(
                    success=False,
                    error="No code provided"
                )

            # Format code
            try:
                code = formatcode(code)
            except ValueError as e:
                return ToolCallResponse(
                    success=False,
                    error=str(e)
                )

            # Validate parameters
            if not (valid := validateparams())[0]:
                return ToolCallResponse(success=False, error=valid[1])

            # Load components
            if not (components := loadcomponents())[0]:
                return ToolCallResponse(success=False, error=components[1])
            log.info(f"ToolCallHandler._methodbuilder | loaded: {components[1]}")

            # Compile code
            if not (compiled := compilecode(code))[0]:
                return ToolCallResponse(success=False, error=compiled[1])

            # Get main function
            if not (func := getmain(compiled[1]))[0]:
                return ToolCallResponse(success=False, error=func[1])

            # Validate function arguments
            if not (args_valid := validateargs(func[1]))[0]:
                return ToolCallResponse(success=False, error=args_valid[1])

            # Execute function
            if not (executed := execute(func[1], args))[0]:
                return ToolCallResponse(success=False, error=executed[1])

            # Convert result
            if not (converted := convert(executed[1]))[0]:
                return ToolCallResponse(success=False, error=converted[1])

            # Validate result
            if not (validated := validateresult(converted[1], components[1]))[0]:
                return ToolCallResponse(success=False, error=validated[1])

            return ToolCallResponse(success=True, data=validated[1])

        except Exception as e:
            log.error(f"ToolCallHandler._methodbuilder | exception | {str(e)}")
            return ToolCallResponse(
                success=False,
                error=f"Methodbuilder Error: {str(e)}"
            )

# global handler instance

toolcallhandler = ToolCallHandler()

"""
for fw in loaded["frameworks"][1:]:
    validator.addstrategy(fw)
    log.debug(f"ToolCallHandler._methodbuilder | added framework strategy: {fw.__class__.__name__}")
"""
