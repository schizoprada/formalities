# ~/formalities/src/formalities/utils/toolcalls.py
from __future__ import annotations
import inspect, typing as t
from dataclasses import dataclass
from formalities.utils.typesys import typehandler
from formalities.utils.discovery import frameworkregistry
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
                            "description": comp.description
                        }
                        for comp in components
                    ]
                }
            )
        except Exception as e:
            log.error(f"ToolCallHandler._matchmaker | exception | {str(e)}")
            return ToolCallResponse(
                success=False,
                error=f"Matchmaker Error: {str(e)}"
            )

    def _methodbuilder(self, query: dict) -> ToolCallResponse:
        try:
            code = query.get("code")
            frameworks = query.get("frameworks", [])
            validators = query.get("validators", [])
            args = query.get("args", {})

            if not code:
                return ToolCallResponse(
                    success=False,
                    error="No code provided"
                )

            loaded = {
                "frameworks": [],
                "validators": []
            }

            for framework in frameworks:
                if (fclass:=self._registry.getcomp(framework)):
                    loaded['frameworks'].append(fclass())

            for validator in validators:
                if (vclass:=self._registry.getcomp(validator)):
                    loaded['validators'].append(vclass())

            namespace = {}
            exec(code, namespace)

            if not (mainfunc:=next((obj for name, obj in namespace.items() if inspect.isfunction(obj)), None)):
                return ToolCallResponse(
                    success=False,
                    error="No function found in the provided code"
                )

            result = mainfunc(**args)

            if not isinstance(result, Proposition):
                conversion = typehandler.toprop(result, "result")
                if not conversion.success:
                    return ToolCallResponse(
                        success=False,
                        error=f"Failed to convert result: {conversion.error}"
                    )
                result = conversion.value

            if not (primaryfw:=(loaded['frameworks'][0] if loaded['frameworks'] else None)):
                return ToolCallResponse(
                    success=False,
                    error="At least one framework required for validation"
                )

            context = ValidationContext(
                framework=primaryfw,
                options=args
            )

            validator = Validator(primaryfw)

            for fw in loaded["frameworks"][1:]:
                validator.addstrategy(fw)

            for v in loaded['validators']:
                validator.addstrategy(v)

            validated = validator.validate(result)

            return ToolCallResponse(
                success=validated.isvalid,
                data=({
                    "result": result,
                    "validation": {
                        "context": context,
                        "history": context.history
                    },
                    "errors": validated.errors
                } if validated.isvalid else None),
                error=("; ".join(validated.errors) if not validated.isvalid else None)
            )

        except Exception as e:
            log.error(f"ToolCallHandler._methodbuilder | exception | {str(e)}")
            return ToolCallResponse(
                success=False,
                error=f"Methodbuilder Error: {str(e)}"
            )

# global handler instance

toolcallhandler = ToolCallHandler()
