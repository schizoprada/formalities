# ~/formalities/src/formalities/fall/runtime/executor.py
import typing as t
from dataclasses import dataclass, field
from loguru import logger as log
from formalities.core.types.propositions import (
    Proposition, AtomicProposition, CompoundProposition
)
from formalities.core.types.operators import (
    ANDN, IMPLIES
)
from formalities.frameworks.simple import ClassicalFramework
from formalities.validation.base import (
    ValidationResult, ValidationContext, Validator
)
from formalities.validation.strategies import (
    LogicalConsistencyStrategy, SyntacticValidationStrategy
)
from formalities.fall.bridges.logic import LogicBridge
from formalities.fall.parser.abstract import (
    Proof, ProofStep, AxiomDefinition
)


@dataclass
class ProofContext:
    """Context for proof execution."""
    bridge: LogicBridge
    givens: dict[str, Proposition] = field(default_factory=dict)
    derived: dict[str, Proposition] = field(default_factory=dict)
    axioms: dict[str, AxiomDefinition] = field(default_factory=dict)
    steps: dict[int, Proposition] = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)
    propsmetadata: dict[str, str] = field(default_factory=dict)
    semantictokens: set[str] = field(default_factory=set)

    def record(self, step: int, action: str, result: bool, error: t.Optional[str] = None) -> None:
        """Record a proof step outcome."""
        self.history.append({
            "step": step,
            "action": action,
            "result": result,
            "error": error
        })

class ProofExecutor:
    """Executes FALL proofs by applying logical operations."""

    def __init__(self, bridge: t.Optional[LogicBridge] = None):
        """Initialize the executor with an optional logic bridge."""
        self.bridge = bridge or LogicBridge()
        self.framework = ClassicalFramework() # this needs to be configurable down the line
        self.validator = Validator(self.framework)
        # also configurability neeeded for validation strategies
        self.validator.addstrategy(SyntacticValidationStrategy())
        self.validator.addstrategy(LogicalConsistencyStrategy())
        self.nlpvalidationenabled = True
        self.debuglevel = 3

    def executeproof(self, proof: Proof, axioms: dict[str, AxiomDefinition], propsmetadata: t.Optional[dict]=None) -> tuple[bool, ProofContext]:
        """Execute a proof and determine if it is valid."""
        # Initialize proof context
        context = ProofContext(self.bridge)
        context.axioms = axioms

        if propsmetadata:
            context.propsmetadata = propsmetadata
            log.debug(f"Loaded proposition metadata: {propsmetadata}")

        # Register givens
        for givenname in proof.given:
            prop = self.bridge.getprop(givenname)
            if not prop:
                log.error(f"Given proposition {givenname} not found")
                context.record(0, f"SETUP:{givenname}", False, f"Proposition not found")
                return False, context
            context.givens[givenname] = prop
            log.debug(f"Registered given proposition: {givenname} = {prop}")

        # Execute each step
        for step in proof.steps:
            success = self._executestep(step, context)
            if not success:
                log.error(f"Step {step.number} failed")
                return False, context

        # Check if we proved the target
        # First check direct match by name in derived propositions
        if proof.prove in context.derived:
            log.info(f"Proof succeeded: {proof.prove} (found in derived propositions)")
            context.record(len(proof.steps) + 1, f"CONCLUSION:{proof.prove}", True)
            return True, context

        # Then check if any step has a matching symbol or represents the target
        for stepnum, prop in context.steps.items():
            # Handle both atomic and compound propositions
            if hasattr(prop, 'symbol') and prop.symbol == proof.prove:
                log.info(f"Proof succeeded: {proof.prove} (matched by symbol)")
                context.record(len(proof.steps) + 1, f"CONCLUSION:{proof.prove}", True)
                return True, context

            # For compound propositions, check if they represent the target in any way
            if not hasattr(prop, 'symbol'):
                # This could be a compound proposition
                # Let's see if this step's result was registered with the target name
                registeredprop = self.bridge.getprop(proof.prove)
                if registeredprop and registeredprop._truthvalue:
                    log.info(f"Proof succeeded: {proof.prove} (registered with truth value)")
                    context.record(len(proof.steps) + 1, f"CONCLUSION:{proof.prove}", True)
                    return True, context

        log.error(f"Proof failed: {proof.prove} not derived")
        context.record(len(proof.steps) + 1, f"CONCLUSION:{proof.prove}", False, "Target not derived")
        return False, context

    def _executestep(self, step: ProofStep, context: ProofContext) -> bool:
        """Execute a single proof step."""
        if step.action.startswith("ASSERT"):
            return self._executeassert(step, context)
        elif step.action.startswith("INFER"):
            return self._executeinfer(step, context)
        else:
            log.error(f"Unknown action: {step.action}")
            context.record(step.number, "UNKNOWN", False, f"Unknown action: {step.action}")
            return False

    def _executeassert(self, step: ProofStep, context: ProofContext) -> bool:
        """Execute an assert step."""
        expr = step.action.replace("ASSERT", "", 1).strip()
        try:
            prop = self.bridge.parseexpression(expr)
            log.debug(f"Parsed assertion expression: {expr} -> {prop}")
            # Validate this assertion given what we know
            evalctx = {}
            for name, p in context.givens.items():
                try:
                    evalctx[name] = p.evaluate()
                    log.debug(f"Added given to eval context: {name} = {evalctx[name]}")
                except ValueError:
                    log.debug(f"Could not evaluate given: {name}")
                    pass
            for name, p in context.derived.items():
                try:
                    evalctx[name] = p.evaluate()
                    log.debug(f"Added derived to eval context: {name} = {evalctx[name]}")
                except ValueError:
                    log.debug(f"Could not evaluate derived: {name}")
                    pass

            # Register the step result
            stepname = f"step{step.number}"
            context.steps[step.number] = prop
            log.debug(f"Registered step {step.number} result: {prop}")

            # Record success
            context.record(step.number, f"ASSERT:{expr}", True)
            return True
        except Exception as e:
            log.error(f"Assert error: {str(e)}")
            context.record(step.number, f"ASSERT:{expr}", False, str(e))
            return False

    def _executeinfer(self, step: ProofStep, context: ProofContext) -> bool:
        """
        Execute an inference step within a proof context, logging detailed operations.
        """
        expr = step.action.replace("INFER", "", 1).strip()
        sources = step.source or []
        via = step.via

        log.debug(f"Executing inference | Step: {step.number} | Expression: {expr} | Sources: {sources} | Via: {via}")
        sourceprops = []

        for sourcename in sources:
            if sourcename in context.givens:
                log.info(f"Source '{sourcename}' found in givens.")
                sourceprops.append(context.givens[sourcename])
                continue

            try:
                if sourcename.startswith("step"):
                    stepnum = int(sourcename[4:])
                    if stepnum in context.steps:
                        log.info(f"Source '{sourcename}' found in previous steps.")
                        sourceprops.append(context.steps[stepnum])
                        continue
            except ValueError:
                log.warning(f"Invalid step reference: {sourcename}")

            if sourcename in context.derived:
                log.info(f"Source '{sourcename}' found in derived conclusions.")
                sourceprops.append(context.derived[sourcename])
                continue

            log.error(f"Source not found: {sourcename}")
            context.record(step.number, f"INFER:{expr}", False, f"Source not found: {sourcename}")
            return False

        if not (axiom := context.axioms.get(via)):
            log.error(f"Axiom not found: {via}")
            context.record(step.number, f"INFER:{expr}", False, f"Axiom not found: {via}")
            return False

        log.info(f"Applying axiom '{via}' to inference.")

        try:
            premises = CompoundProposition(ANDN(len(sourceprops)), tuple(sourceprops))
            conclusion = AtomicProposition(expr, _truthvalue=True)

            log.debug(f"Validating inference | Premises: {premises} | Conclusion: {conclusion}")
            validationresult, _ = self.validator.validate(CompoundProposition(IMPLIES(), (premises, conclusion)))

            if validationresult.isvalid:
                log.info(f"Inference valid | Step: {step.number} | Expression: {expr}")
                context.steps[step.number] = conclusion
                context.derived[expr] = conclusion

                if hasattr(self.bridge, 'registerprop'):
                    self.bridge.registerprop(expr, conclusion)

                context.record(step.number, f"INFER:{expr} VIA:{via}", True)
                return True
            else:
                log.warning(f"Inference failed | Step: {step.number} | Errors: {'; '.join(validationresult.errors)}")
                context.record(step.number, f"INFER:{expr}", False, "; ".join(validationresult.errors))
                return False
        except Exception as e:
            log.exception(f"Exception during inference execution | Step: {step.number} | Error: {e}")
            context.record(step.number, f"INFER:{expr}", False, str(e))
            return False

    def getaxiompreconditions(self, axiom: AxiomDefinition) -> t.List[Proposition]:
        """
        Extract preconditions from an axiom as propositions, logging processed axiom and extracted conditions.
        """
        log.debug(f"Processing axiom: {axiom.name}")
        result = []

        for condition in axiom.conditions:
            try:
                prop = self.bridge.parseexpression(condition.expression)
                result.append(prop)
                log.info(f"Extracted precondition from axiom '{axiom.name}': {condition.expression}")
            except Exception as e:
                log.error(f"Failed to parse axiom condition '{condition.expression}' in '{axiom.name}': {str(e)}")

        log.debug(f"Completed axiom processing: {axiom.name} | Extracted Preconditions: {result}")
        return result



'''
def _executeinfer(self, step, context):
    """Execute an infer step with semantic validation."""
    expr = step.action.replace("INFER", "", 1).strip()
    log.debug(f"Executing inference step {step.number}: {expr}")

    # Validate that all sources and axiom exist
    if not step.source:
        log.error(f"Step {step.number} has no sources")
        context.record(step.number, f"INFER:{expr}", False, "No sources specified")
        return False

    if not step.via:
        log.error(f"Step {step.number} has no axiom")
        context.record(step.number, f"INFER:{expr}", False, "No axiom specified")
        return False

    # Get the axiom
    axiom = context.axioms.get(step.via)
    if not axiom:
        log.error(f"Axiom not found: {step.via}")
        context.record(step.number, f"INFER:{expr}", False, f"Axiom not found: {step.via}")
        return False

    # Get the source propositions
    sourceprops = []
    sourcemeta = []
    for sourcename in step.source:
        # Check if source is a given
        if sourcename in context.givens:
            sourceprops.append(context.givens[sourcename])
            if sourcename in context.propsmetadata:
                sourcemeta.append(context.propsmetadata[sourcename])
            log.debug(f"Using given source: {sourcename}")
            continue

        # Check if source is derived
        if sourcename in context.derived:
            sourceprops.append(context.derived[sourcename])
            if sourcename in context.propsmetadata:
                sourcemeta.append(context.propsmetadata[sourcename])
            log.debug(f"Using derived source: {sourcename}")
            continue

        # Check if source is a previous step
        stepnum = None
        try:
            if sourcename.startswith("step"):
                stepnum = int(sourcename[4:])
                if stepnum in context.steps:
                    sourceprops.append(context.steps[stepnum])
                    log.debug(f"Using step source: {sourcename}")
                    continue
        except ValueError:
            pass
        log.error(f"Source not found: {sourcename}")
        context.record(step.number, f"INFER:{expr}", False, f"Source not found: {sourcename}")
        return False

    # Check if NLP bridge is available and enabled
    validinference = True
    reason = "Structural validation only"

    # Check if the LogicBridge has an NLP bridge attached
    # In _executeinfer method, add this debugging right before checking for NLP bridge
    log.info(f"Checking for NLP bridge: hasattr={hasattr(self.bridge, 'nlpbridge')}, enabled={getattr(self.bridge, 'nlpbridge', None) and getattr(self.bridge.nlpbridge, 'enabled', False)}")
    if hasattr(self.bridge, 'nlpbridge') and self.bridge.nlpbridge:
        bridge = self.bridge.nlpbridge
        log.info(f"NLP bridge found: enabled={bridge.enabled}")
        if bridge.enabled:
            # Get or create target proposition
            targetprop = self.bridge.getprop(expr)
            if not targetprop:
                # Try to create a new one with the structure from existing props
                from formalities.core.types.propositions.atomic import AtomicProposition
                targetprop = AtomicProposition(expr)

            # Validate using NLP bridge
            validationresult = self.bridge.nlpbridge.validateinference(sourceprops, targetprop)
            validinference = validationresult.valid
            reason = validationresult.reason

            # Log the validation details
            log.info(f"NLP validation result: valid={validinference}, confidence={validationresult.confidence:.2f}")
            if validationresult.connections:
                log.info(f"Semantic connections: {validationresult.connections}")

    try:
        # Instead of attempting to modify an existing proposition, create a new one with the truth value
        from formalities.core.types.propositions.atomic import AtomicProposition

        # Create a new version with the truth value set based on validation
        resultprop = AtomicProposition(expr, _truthvalue=validinference)

        # Register the result
        stepname = f"step{step.number}"
        context.steps[step.number] = resultprop

        if validinference:
            context.derived[expr] = resultprop
            # Also register in the bridge for future reference
            self.bridge.registerprop(expr, resultprop)
            context.record(step.number, f"INFER:{expr} via {step.via}", True)
            log.info(f"Successfully inferred {expr} in step {step.number}")
            return True
        else:
            context.record(step.number, f"INFER:{expr}", False, reason)
            log.warning(f"Failed to infer {expr} in step {step.number}: {reason}")
            return False

    except Exception as e:
        log.error(f"Inference error: {str(e)}")
        context.record(step.number, f"INFER:{expr}", False, str(e))
        return False
'''
