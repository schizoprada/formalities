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
    exception: t.Optional[Exception] = None


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
                error=f"Matchmaker Error: {str(e)}",
                exception=e
            )

    def _methodbuilder(self, query: dict) -> ToolCallResponse:
        """Enhanced method builder with pre-execution validation"""

        def validateparams() -> tuple[bool, (str | None), (Exception | None)]:
            """validate input parameters"""
            if (errors := typehandler.validateparams(query,
                {
                    "code": str,
                    "frameworks": list,
                    "validators": list
                }
            )):
                errormsg = f"Parameter validation failed: {'; '.join(errors)}"
                return False, errormsg, ValueError(errormsg)
            return True, None, None

        def compilecode(code: str) -> tuple[bool, (dict | str), (Exception | None)]:
            """Compile code and return namespace"""
            namespace = {}
            try:
                exec(code, namespace)
                return True, namespace, None
            except Exception as e:
                return False, f"Code Compilation Error: {str(e)}", e

        def getmain(namespace: dict) -> tuple[bool, (t.Callable | str), (Exception | None)]:
            """Get main function from namespace"""
            if (mainfunc := next((
                obj for name, obj in namespace.items()
                if inspect.isfunction(obj)
            ), None)):
                return True, mainfunc, None
            error = "No function found in the provided code"
            return False, error, ValueError(error)

        def validateargs(func: t.Callable) -> tuple[bool, (str | None), (Exception | None)]:
            """Validate function arguments"""
            sig = inspect.signature(func)
            required = {
                name: param.annotation
                for name, param in sig.parameters.items()
                if param.default == param.empty
            }
            if (missing := [name for name in required if name not in query.get('args', {})]):
                errormsg = f"Missing required arguments: {', '.join(missing)}"
                return False, errormsg, ValueError(errormsg)
            return True, None, None

        def loadcomponents() -> tuple[bool, (dict | str), (Exception | None)]:
            """Load frameworks and validators"""
            loaded = {"frameworks": [], "validators": []}
            for framework in query.get("frameworks", []):
                if (fclass := self._registry.getcomp(framework)):
                    loaded["frameworks"].append(fclass())
                else:
                    errormsg = f"Framework not found: {framework}"
                    return False, errormsg, ImportError(errormsg)
            for validator in query.get("validators", []):
                if (vclass := self._registry.getcomp(validator)):
                    loaded["validators"].append(vclass())
                else:
                    errormsg = f"Validator not found: {validator}"
                    return False, errormsg, ImportError(errormsg)
            if not loaded["frameworks"]:
                errormsg = "At least one framework is required for validation"
                return False, errormsg, ValueError(errormsg)
            return True, loaded, None

        def execute(func: t.Callable, args: dict) -> tuple[bool, t.Any, (Exception | None)]:
            """Execute function with arguments"""
            try:
                result = func(**args)
                return True, result, None
            except Exception as e:
                return False, f"Function Execution Error: {str(e)}", e

        def convert(result: t.Any) -> tuple[bool, (Proposition | str), (Exception | None)]:
            """Convert result to proposition"""
            if isinstance(result, Proposition):
                return True, result, None
            conversion = typehandler.toprop(result, "result")
            if not conversion.success:
                errormsg = f"Failed to convert result: {conversion.error}"
                return False, errormsg, TypeError(errormsg)
            return True, conversion.value, None

        def validateresult(result: Proposition, components: dict) -> tuple[bool, (dict | str), (Exception | None)]:
            """Validate result using components"""
            try:
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
                    errormsg = "; ".join(validated.errors)
                    return False, errormsg, ValueError(errormsg)
                return True, {
                    "result": result,
                    "validation": {
                        "context": valctx,
                        "history": valctx.history
                    },
                    "errors": validated.errors
                }, None
            except Exception as e:
                return False, f"Validation Error: {str(e)}", e

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
                errormsg = "No code provided"
                return ToolCallResponse(
                    success=False,
                    error=errormsg,
                    exception=ValueError(errormsg)
                )

            # Format code
            try:
                code = formatcode(code)
            except ValueError as e:
                return ToolCallResponse(
                    success=False,
                    error=str(e),
                    exception=e
                )

            # Validate parameters
            valid, errormsg, validationexc = validateparams()
            if not valid:
                return ToolCallResponse(success=False, error=errormsg, exception=validationexc)

            # Load components
            valid, componentsresult, componentsexc = loadcomponents()
            if not valid:
                return ToolCallResponse(success=False, error=componentsresult, exception=componentsexc)
            log.info(f"ToolCallHandler._methodbuilder | loaded: {componentsresult}")

            # Compile code
            valid, compiledresult, compileexc = compilecode(code)
            if not valid:
                return ToolCallResponse(success=False, error=compiledresult, exception=compileexc)

            # Get main function
            valid, funcresult, funcexc = getmain(compiledresult)
            if not valid:
                return ToolCallResponse(success=False, error=funcresult, exception=funcexc)

            # Validate function arguments
            valid, argserror, argsexc = validateargs(funcresult)
            if not valid:
                return ToolCallResponse(success=False, error=argserror, exception=argsexc)

            # Execute function
            valid, executedresult, execexc = execute(funcresult, args)
            if not valid:
                return ToolCallResponse(success=False, error=executedresult, exception=execexc)

            # Convert result
            valid, convertedresult, convertexc = convert(executedresult)
            if not valid:
                return ToolCallResponse(success=False, error=convertedresult, exception=convertexc)

            # Validate result
            valid, validatedresult, validationexc = validateresult(convertedresult, componentsresult)
            if not valid:
                return ToolCallResponse(success=False, error=validatedresult, exception=validationexc)

            return ToolCallResponse(success=True, data=validatedresult)

        except Exception as e:
            log.error(f"ToolCallHandler._methodbuilder | exception | {str(e)}")
            return ToolCallResponse(
                success=False,
                error=f"Methodbuilder Error: {str(e)}",
                exception=e
            )

# global handler instance
toolcallhandler = ToolCallHandler()
