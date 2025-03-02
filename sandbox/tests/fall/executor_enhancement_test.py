# ~/formalities/sandbox/tests/fall/executor_enhancement_test.py
"""Example code for enhancing the ProofExecutor for semantic validation."""

# This file demonstrates the recommended changes to ProofExecutor._executeinfer
# to properly integrate semantic validation into the inference process.

from formalities.fall.runtime.executor import ProofExecutor, ProofContext
from formalities.fall.parser.abstract import ProofStep
from formalities.core.types.propositions import Proposition, AtomicProposition, CompoundProposition
from formalities.core.types.operators.boolean import IMPLIES, AND
from formalities.validation.base import ValidationResult
from loguru import logger as log

def enhanced_execute_infer(self, step: ProofStep, context: ProofContext) -> bool:
    """Enhanced version of the _executeinfer method that integrates NLP validation."""
    expr = step.action.replace("INFER", "", 1).strip()
    sources = (step.source or [])
    via = step.via

    log.info(f"Executing inference step {step.number}: {expr}")
    log.info(f"Sources: {sources}, Axiom: {via}")

    # Validate that all sources and axiom exist
    if not sources:
        log.error(f"Step {step.number} has no sources")
        context.record(step.number, f"INFER:{expr}", False, "No sources specified")
        return False

    if not via:
        log.error(f"Step {step.number} has no axiom")
        context.record(step.number, f"INFER:{expr}", False, "No axiom specified")
        return False

    # Get the axiom
    axiom = context.axioms.get(via)
    if not axiom:
        log.error(f"Axiom not found: {via}")
        context.record(step.number, f"INFER:{expr}", False, f"Axiom not found: {via}")
        return False

    # Get the source propositions
    sourceprops = []
    for sourcename in sources:
        # Check if source is a given
        if sourcename in context.givens:
            sourceprops.append(context.givens[sourcename])
            log.debug(f"Using given source: {sourcename}")
            continue

        # Check if source is derived
        if sourcename in context.derived:
            sourceprops.append(context.derived[sourcename])
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

    # Create target proposition
    targetprop = AtomicProposition(expr, _truthvalue=True)

    # Structural validation using Formalities
    try:
        log.info("Performing structural validation")
        # Create logical implication for validation
        premises = None
        if len(sourceprops) == 1:
            premises = sourceprops[0]
        else:
            premises = CompoundProposition(AND(len(sourceprops)), tuple(sourceprops))

        implication = CompoundProposition(IMPLIES(), (premises, targetprop))

        # Validate using framework
        valid_result, _ = self.validator.validate(implication)
        structural_valid = valid_result.isvalid

        log.info(f"Structural validation result: {structural_valid}")
        if not structural_valid:
            errors = valid_result.errors
            log.error(f"Structural validation failed: {errors}")
            context.record(step.number, f"INFER:{expr}", False, f"Structural error: {'; '.join(errors)}")
            return False
    except Exception as e:
        log.error(f"Structural validation error: {str(e)}")
        context.record(step.number, f"INFER:{expr}", False, f"Validation error: {str(e)}")
        return False

    # Semantic validation using NLP bridge
    semantic_valid = True
    reason = "Structural validation only"

    if hasattr(self.bridge, 'nlpbridge') and self.bridge.nlpbridge and self.bridge.nlpbridge.enabled:
        bridge = self.bridge.nlpbridge
        log.info(f"Performing semantic validation with NLP bridge (enabled={bridge.enabled})")

        # Add text attributes if not present
        for i, prop in enumerate(sourceprops):
            if not hasattr(prop, 'text'):
                # Use a fallback text representation
                setattr(prop, 'text', f"Proposition {sources[i]}")

        if not hasattr(targetprop, 'text'):
            setattr(targetprop, 'text', f"Proposition {expr}")

        # Validate using NLP bridge
        validation_result = bridge.validateinference(sourceprops, targetprop)
        semantic_valid = validation_result.valid
        reason = validation_result.reason
        confidence = validation_result.confidence

        # Track common tokens in context
        if hasattr(validation_result, 'commontokens'):
            context.semantictokens.update(validation_result.commontokens)

        log.info(f"Semantic validation result: valid={semantic_valid}, confidence={confidence:.2f}")
        if validation_result.connections:
            log.info(f"Semantic connections: {validation_result.connections}")

    # Final validation result combines structural and semantic
    valid_inference = structural_valid and semantic_valid

    if valid_inference:
        # Register the inferred proposition
        context.steps[step.number] = targetprop
        context.derived[expr] = targetprop

        # Also register in the bridge for future reference
        if hasattr(self.bridge, 'registerprop'):
            self.bridge.registerprop(expr, targetprop)

        context.record(step.number, f"INFER:{expr} via {via}", True)
        log.info(f"Successfully inferred {expr} in step {step.number}")
        return True
    else:
        context.record(step.number, f"INFER:{expr}", False, reason)
        log.warning(f"Failed to infer {expr} in step {step.number}: {reason}")
        return False

# Note: This method should be incorporated into ProofExecutor class
# It's shown here for demonstration purposes
