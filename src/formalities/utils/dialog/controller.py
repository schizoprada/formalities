# ~/formalities/src/formalities/utils/dialog/controller.py
from __future__ import annotations
import typing as t
from abc import ABC, abstractmethod
from enum import Enum, auto
from dataclasses import dataclass, field
from formalities.utils.toolcalls import toolcallhandler, ToolCallRequest, ToolCallResponse
from formalities.utils.dialog.state import DialogState, DialogStage, ErrorType
from loguru import logger as log

class DialogAction(Enum):
    CONTINUE = auto()
    RETRY = auto()
    FALLBACK = auto()
    ESCALATE = auto()
    TERMINATE = auto()


@dataclass
class DialogRequest:
    content: str
    role: str = "user"
    metadata: dict[str, t.Any] = field(default_factory=dict)


@dataclass
class DialogResponse:
    content: str
    action: DialogAction = DialogAction.CONTINUE
    metadata: dict[str, t.Any] = field(default_factory=dict)
    suggestedtools: list[str] = field(default_factory=list)

class DialogStrategy(ABC):

    @abstractmethod
    def apply(self, state: DialogState, request: DialogRequest) -> DialogResponse:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def handleablestages(self) -> list[DialogStage]:
        pass

    def canhandle(self, state: DialogState) -> bool:
        return state.stage in self.handleablestages


class DialogController:
    def __init__(self):
        self.state = DialogState()
        self.strategies: list[DialogStrategy] = []

    def registerstrategy(self, strategy: DialogStrategy) -> None:
        self.strategies.append(strategy)
        #log.info(f"Registered strategy: {strategy.name}")

    def processrequest(self, request: DialogRequest) -> DialogResponse:
        self.state.history.addexchange(request.role, request.content, request.metadata)
        for strategy in self.strategies:
            if strategy.canhandle(self.state):
                log.info(f"Applying strategy: {strategy.name} for stage: {self.state.stage.name}")
                try:
                    response = strategy.apply(self.state, request)
                    self.state.history.addexchange("system", response.content, response.metadata)
                    return response
                except Exception as e:
                    log.exception(f"Error in strategy {strategy.name}: {str(e)}")
                    self.state.seterror(e)
                    # Retry with error handling strategy
                    for errorstrategy in self.strategies:
                        if DialogStage.ERRORHANDLING in errorstrategy.handleablestages:
                            return errorstrategy.apply(self.state, request)
                    # If no error handling strategy, return fallback
                    return DialogResponse(
                        content=f"An error occurred: {str(e)}",
                        action=DialogAction.FALLBACK
                    )

        log.warning(f"No strategy found for stage: {self.state.stage.name}")
        return DialogResponse(
            content="I'm not sure how to proceed at this stage.",
            action=DialogAction.FALLBACK
        )

    def handletoolcall(self, name: str, args: dict) -> t.Any:
        log.info(f"Handling tool call: {name} with args: {args}")
        try:
            response = None
            match name:
                case "matchmaker":
                    response = toolcallhandler._matchmaker(args)
                case "methodbuilder":
                    response = toolcallhandler._methodbuilder(args)
                case _:
                    raise ValueError(f"Unknown tool: {name}")

            rdata = response.data if response.success else {"error": response.error}
            self.state.memory.addtoolcall(name, args, rdata, response.success)

            if not response.success:
                # Use the exception object directly if available
                if response.exception:
                    self.state.seterror(response.exception)
                else:
                    # Create exception from error message if none provided
                    self.state.seterror(Exception(response.error))

                return {"error": response.error}

            return response.data

        except Exception as e:
            log.error(f"Error executing tool call: {name}")
            self.state.seterror(e)
            return {"error": f"Tool execution error: {str(e)}"}


    def reset(self) -> None:
        self.state.reset()
        log.info(f"Dialog controller reset")


# global instance
dialogcontroller = DialogController()
