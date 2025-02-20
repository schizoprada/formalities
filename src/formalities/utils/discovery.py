# ~/formalities/src/formalities/utils/discovery.py
from __future__ import annotations
import inspect, importlib, typing as t
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from formalities.frameworks.base import Framework
from formalities.validation.base import ValidationStrategy
from formalities.core.types.logic import LogicType
from formalities.core.types.operators.base import Operator
from loguru import logger as log

@dataclass
class ComponentInfo:
    """Information about a discoverable framework component"""
    name: str
    typeof: str # framework, validator, operator, etc
    description: str
    modulepath: str
    classname: str
    baseclasses: list[str] = field(default_factory=list)
    requirements: list[str] = field(default_factory=list)


class FrameworkRegistry:
    """Central registry for framework components"""

    def __init__(self):
        self._components: dict[str, ComponentInfo] = {}
        self._frameworkpath = Path(__file__).parent.parent


    def _registercomp(self, name: str, cls: t.Type, comptype: str, modulepath: str) -> None:
        """Register a component with its metadata"""
        self._components[name] = ComponentInfo(
            name=name,
            typeof=comptype,
            description=(cls.__doc__ or ""),
            modulepath=modulepath,
            classname=cls.__name__,
            baseclasses=[base.__name__ for base in cls.__bases__]
        )

    def _conditionalregister(self, name: str, obj: t.Any, modulepath: str) -> None:
        typeof = None
        if issubclass(obj, Framework) and obj != Framework:
            typeof = "framework"
        elif issubclass(obj, ValidationStrategy) and obj != ValidationStrategy:
            typeof = "validator"
        elif issubclass(obj, Operator) and obj != Operator:
            typeof = "operator"
        if typeof:
            self._registercomp(name, obj, typeof, modulepath)

    def _scandir(self, path: Path) -> None:
        """Recursively scan a directory for components"""
        for item in path.rglob("*.py"):
            if item.name.startswith("__"):
                continue
            modulepath = str(item.relative_to(self._frameworkpath.parent)).replace("/", ".").replace(".py", "")
            try:
                module = importlib.import_module(modulepath)
                for name, obj in inspect.getmembers(module):
                    if inspect.isclass(obj):
                        self._conditionalregister(name, obj, modulepath)
            except ImportError as e:
                log.error(f"FrameworkRegistry._scandir | failed to import {modulepath} | {str(e)}")


    def discoverall(self) -> None:
        self._scandir(self._frameworkpath)


    def getcomp(self, name: str) -> t.Optional[t.Type]:
        if name not in self._components:
            return None
        info = self._components[name]
        module = importlib.import_module(info.modulepath)
        return getattr(module, info.classname)

    def query(self, comptype: t.Optional[str] = None, baseclass: t.Optional[str] = None, keyword: t.Optional[str] = None) -> list[ComponentInfo]:
        results = []
        for info in self._components.values():
            matches = True
            if comptype and info.typeof != comptype:
                matches = False
            if baseclass and baseclass not in info.baseclasses:
                matches = False
            if keyword and keyword.lower() not in info.description.lower():
                matches = False
            if matches:
                results.append(info)
        return results


frameworkregistry = FrameworkRegistry()
frameworkregistry.discoverall()
