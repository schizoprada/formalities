# ~/formalities/src/formalities/fall/runtime/interpreter.py
import typing as t
from formalities.fall.parser.abstract import (
    Node, Program, RuleDefinition, AxiomDefinition,
    PropositionDefinition, Assertion, Proof, ProofStep, Query, Condition, Visitor
)
from formalities.fall.bridges.logic import LogicBridge
from formalities.fall.runtime.validator import FallValidator
from formalities.fall.runtime.executor import ProofExecutor
from loguru import logger as log

class Environment:
    """Environment for storing variables and definitions during execution."""

    def __init__(self):
        # Initialize the logic bridge
        self.bridge = LogicBridge()

        # Initialize validators and executors
        self.validator = FallValidator(self.bridge)
        self.executor = ProofExecutor(self.bridge)

        # Storage for language constructs
        self.rules = {}
        self.axioms = {}
        self.propositions = {}
        self.assertions = []
        self.proofs = []
        self.output = []

    def definerule(self, name: str, rule: RuleDefinition) -> None:
        """Define a rule with validation."""
        validation = self.validator.validaterule(rule)
        if validation.isvalid:
            self.rules[name] = rule
            self.output.append(f"Defined rule: {name}")
        else:
            self.output.append(f"Invalid rule {name}: {'; '.join(validation.errors)}")

    def defineaxiom(self, name: str, axiom: AxiomDefinition) -> None:
        """Define an axiom with validation."""
        validation = self.validator.validateaxiom(axiom)
        if validation.isvalid:
            self.axioms[name] = axiom
            self.output.append(f"Defined axiom: {name}")

            # Also register with the validation context
            self.validator.context.axioms[name] = axiom
        else:
            self.output.append(f"Invalid axiom {name}: {'; '.join(validation.errors)}")

    def defineproposition(self, name: str, prop: PropositionDefinition) -> None:
        """Define a proposition with validation."""
        validation = self.validator.validateproposition(prop)
        if validation.isvalid:
            self.propositions[name] = prop

            # Create a logical proposition and register it
            logicalprop = self.bridge.createproposition(name)
            self.output.append(f"Defined proposition: {name} as '{prop.text}'")
        else:
            self.output.append(f"Invalid proposition {name}: {'; '.join(validation.errors)}")

    def addassertion(self, assertion: Assertion) -> None:
        """Add an assertion with validation."""
        validation = self.validator.validateassertion(assertion)
        if validation.isvalid:
            self.assertions.append(assertion)
            self.output.append(f"Asserted: {assertion.expression}")

            # Parse and evaluate the expression
            try:
                prop = self.bridge.parseexpression(assertion.expression)
                result = self.bridge.evaluate(prop)
                self.output.append(f"Evaluation: {result}")
            except Exception as e:
                self.output.append(f"Evaluation error: {str(e)}")
        else:
            self.output.append(f"Invalid assertion: {'; '.join(validation.errors)}")

    def executeproof(self, proof: Proof) -> None:
        """Execute a proof with validation."""
        validation = self.validator.validateproof(proof)
        if validation.isvalid:
            self.output.append(f"Validating proof from {', '.join(proof.given)} to {proof.prove} using {', '.join(proof.using)}")

            # Execute the proof
            success, context = self.executor.executeproof(proof, self.axioms)

            if success:
                self.output.append(f"Proof succeeded! Established: {proof.prove}")
                self.proofs.append(proof)
            else:
                self.output.append(f"Proof failed. Check the steps and logic.")

            # Output step history
            for entry in context.history:
                if entry.get("error"):
                    self.output.append(f"Step {entry['step']}: {entry['action']} - FAILED: {entry['error']}")
                else:
                    self.output.append(f"Step {entry['step']}: {entry['action']} - SUCCESS")
        else:
            self.output.append(f"Invalid proof: {'; '.join(validation.errors)}")

    def resolvequery(self, query: Query) -> t.Optional[bool]:
        """Resolve a query against the current knowledge base."""
        propname = query.proposition

        # Check if it's a defined proposition
        if propname in self.propositions:
            self.output.append(f"Proposition {propname} exists")

            # Get the corresponding logical proposition
            logicalprop = self.bridge.getprop(propname)
            if logicalprop:
                try:
                    # Try to evaluate directly (will work if truth value is set)
                    result = logicalprop.evaluate()
                    self.output.append(f"Evaluation: {result}")
                    return result
                except ValueError as e:
                    # If we get here, the proposition exists but has no direct truth value

                    # Check if it has been established in any proof
                    for proof in self.proofs:
                        if proof.prove == propname:
                            self.output.append(f"Proposition {propname} was established by proof")
                            # Since it was proven, we can set its truth value and re-attempt evaluation
                            if hasattr(logicalprop, '_truthvalue'):
                                # Use direct attribute access to bypass frozen dataclass restrictions
                                object.__setattr__(logicalprop, '_truthvalue', True)                 # Use direct attribute access to bypass frozen dataclass restrictions
                                try:
                                    result = logicalprop.evaluate()
                                    self.output.append(f"Evaluation after proof: {result}")
                                    return result
                                except Exception:
                                    # If evaluation still fails, just return True since it was proven
                                    return True
                            return True

                    # Check if we have a derived proposition with this name
                    for name, prop in self.bridge._propositions.items():
                        if name == propname:
                            # Try to evaluate, but handle the case where it might not have a truth value
                            try:
                                value = prop.evaluate()
                                self.output.append(f"Proposition {propname} was derived with value: {value}")
                                return value
                            except ValueError:
                                # No truth value available
                                pass

                    self.output.append(f"Cannot evaluate: {str(e)}")
                except Exception as e:
                    self.output.append(f"Error during evaluation: {str(e)}")

            return None

        # Check if it can be derived from proofs
        for proof in self.proofs:
            if proof.prove == propname:
                self.output.append(f"Proposition {propname} is proven")
                return True

        self.output.append(f"Unknown proposition: {propname}")
        return False

    def getoutput(self) -> str:
        """Get the accumulated output as a string."""
        result = "\n".join(self.output)
        self.output = []  # Clear output after reading
        return result

class Interpreter(Visitor):
    """FALL language interpreter."""

    def __init__(self):
        self.environment = Environment()

    def interpret(self, program: Program) -> None:
        """Interpret a FALL program."""
        program.accept(self)

    def _execute(self, node: Node) -> None:
        """Execute a node by visiting it."""
        node.accept(self)

    def visitruledef(self, node: RuleDefinition) -> None:
        """Visit a rule definition."""
        self.environment.definerule(node.name, node)

    def visitaxiomdef(self, node: AxiomDefinition) -> None:
        """Visit an axiom definition."""
        self.environment.defineaxiom(node.name, node)

    def visitpropdef(self, node: PropositionDefinition) -> None:
        """Visit a proposition definition."""
        #log.debug(f"Defining Proposition: {node.name}")
        # Try to use NLP bridge to enhance the proposition's structure
        try:
            from formalities.fall.bridges.nlp import NLPBridge
            nlp = NLPBridge()
            if 'structure' not in node.structure:
                extracted = nlp.extractstructure(node.text)
                structdict = {
                    'subject': extracted.subject,
                    'verb': extracted.verb,
                    'objects': extracted.objects,
                    'modifiers': extracted.modifiers
                }
                # Add NLP-extracted structure to the proposition's structure
                node.structure['nlpstructure'] = str(structdict)
                #log.debug(f"Enhanced proposition with NLP structure: {structdict}")
        except Exception as e:
            #log.error(f"NLP enhancement failed: {str(e)}")
            pass
        self.environment.defineproposition(node.name, node)

    def visitassertion(self, node: Assertion) -> None:
        """Visit an assertion."""
        self.environment.addassertion(node)

    def visitproof(self, node: Proof) -> None:
        """Visit a proof."""
        self.environment.executeproof(node)
        for step in node.steps:
            step.accept(self)

    def visitproofstep(self, node: ProofStep) -> None:
        """Visit a proof step."""
        # Steps are processed together in the proof execution
        pass

    def visitquery(self, node: Query) -> None:
        """Visit a query."""
        #log.debug(f"Querying Proposition: {node.proposition}")
        #log.debug(f"Known Propositions: {list(self.environment.propositions.keys())}")
        self.environment.resolvequery(node)

    def visitprogram(self, node: Program) -> None:
        """Visit the program node."""
        #log.debug(f"Visiting Program with {len(node.statements)} Statements")
        for statement in node.statements:
            #log.debug(f"Executing Statement of type: {type(statement).__name__}")
            statement.accept(self)

    def visitcondition(self, node: Condition) -> None:
        """Visit a condition."""
        pass  # Conditions are processed within their containing nodes
