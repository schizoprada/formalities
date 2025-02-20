# ~/formalities/src/formalities/utils/toolcalls.py
from __future__ import annotations
import inspect, typing as t
from dataclasses import dataclass
from formalities.utils.discovery import frameworkregistry
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

            validations = []
            for fw in loaded['frameworks']:
                validations.append(
                    fw.validate(result)
                )
            for vl in loaded['validators']:
                validations.append(
                    vl.validate(result, None)
                )
            return ToolCallResponse(
                success=True,
                data={
                    "result": result,
                    "validations": validations
                }
            )
        except Exception as e:
            log.error(f"ToolCallHandler._methodbuilder | exception | {str(e)}")
            return ToolCallResponse(
                success=False,
                error=f"Methodbuilder Error: {str(e)}"
            )

# global handler instance

toolcallhandler = ToolCallHandler()
