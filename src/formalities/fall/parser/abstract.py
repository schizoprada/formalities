from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

class Node(ABC):
    """Base class for all AST nodes."""

    @abstractmethod
    def accept(self, visitor):
        """Accept a visitor to process this node."""
        pass

class Visitor(ABC):
    """Base visitor interface for AST traversal."""

    @abstractmethod
    def visitruledef(self, node):
        pass

    @abstractmethod
    def visitaxiomdef(self, node):
        pass

    @abstractmethod
    def visitpropdef(self, node):
        pass

    @abstractmethod
    def visitassertion(self, node):
        pass

    @abstractmethod
    def visitproof(self, node):
        pass

    @abstractmethod
    def visitquery(self, node):
        pass

@dataclass
class Condition(Node):
    """A condition in a rule or axiom definition."""
    expression: str

    def accept(self, visitor):
        return visitor.visitcondition(self)

@dataclass
class RuleDefinition(Node):
    """Definition of a grammatical rule."""
    name: str
    conditions: List[Condition]

    def accept(self, visitor):
        return visitor.visitruledef(self)

@dataclass
class AxiomDefinition(Node):
    """Definition of a logical axiom."""
    name: str
    conditions: List[Condition]

    def accept(self, visitor):
        return visitor.visitaxiomdef(self)

@dataclass
class PropositionDefinition(Node):
    """Definition of a proposition from natural language."""
    name: str
    text: str
    structure: Dict[str, Any]

    def accept(self, visitor):
        return visitor.visitpropdef(self)

@dataclass
class Assertion(Node):
    """Logical assertion between propositions."""
    expression: str

    def accept(self, visitor):
        return visitor.visitassertion(self)

@dataclass
class ProofStep(Node):
    """A step in a proof process."""
    number: int
    action: str
    source: Optional[List[str]] = None
    via: Optional[str] = None

    def accept(self, visitor):
        return visitor.visitproofstep(self)

@dataclass
class Proof(Node):
    """A complete proof process."""
    given: List[str]
    prove: str
    using: List[str]
    steps: List[ProofStep]

    def accept(self, visitor):
        return visitor.visitproof(self)

@dataclass
class Query(Node):
    """A query to the knowledge base."""
    proposition: str

    def accept(self, visitor):
        return visitor.visitquery(self)

@dataclass
class Program(Node):
    """The root node of a FALL program."""
    statements: List[Node]

    def accept(self, visitor):
        return visitor.visitprogram(self)
