# FALL System Refactoring Plan: Integrating Formalities Core Components

## Phase 1: Foundation Integration with Formalities

### Core Integration
- [x] Review existing `formalities.core.types` components:
  - [x] Assess reusability of `Proposition`, `Atomic`, `Compound` classes
  - [x] Map `formalities.core.types.propositions` to FALL propositions
  - [ ] Identify which predicate logic components can be reused

### Bridge to Formalities Logic System
- [x] Update `bridges/logic.py`:
  - [x] Create adapter for `formalities.core.types.operators`
  - [x] Integrate with `formalities.frameworks.simple.ClassicalFramework`
  - [x] Connect with `formalities.validation` components

### NLP Bridge Enhancement
- [x] Enhance `bridges/nlp.py`:
  - [x] Add methods to translate natural language to logical structures
  - [x] Connect NLP extraction to `formalities.core` propositions
  - [x] Add identification of quantifiers, variables, and relationships

## Phase 2: Logic Rule Integration

### Inference Rule Integration
- [x] Integrate `formalities.core.types.operators` inference rules:
  - [ ] Map to Universal instantiation (∀x P(x) → P(c))
  - [x] Map to Modus ponens (P → Q, P ⊢ Q)
  - [x] Map to other logical operators and rules
  - [ ] Create adapter for `formalities.core.types.operators.modal` if needed

### Validation System Connection
- [x] Connect to `formalities.validation`:
  - [x] Use `ValidationStrategy` for inference validation
  - [x] Adapt `ValidationContext` for FALL proof tracking
  - [x] Leverage existing validators for logical consistency

## Phase 3: Parser and Grammar Updates

### Parser Enhancements
- [ ] Update `parser/abstract.py`:
  - [ ] Add AST nodes for predicate expressions
  - [ ] Create mapping between AST and `formalities.core.types`

- [ ] Modify `parser/parsing.py`:
  - [ ] Enhance to handle predicate logic syntax
  - [ ] Connect parsed structures to formalities types

### Grammar Extension
- [ ] Update `grammar/keywords.py`:
  - [ ] Add tokens for logical operations that match formalities
  - [ ] Support for predicate logic notation

## Phase 4: Runtime Execution System

### Executor Updates
- [x] Refactor `runtime/executor.py`:
  - [x] Use `formalities.core.types` for proposition representation
  - [x] Implement inference verification using formalities validation
  - [x] Connect NLP bridge output to logical frameworks

### Interpreter Enhancement
- [ ] Update `runtime/interpreter.py`:
  - [ ] Use `formalities.frameworks` for underlying reasoning
  - [ ] Connect to `formalities.utils.toolcalls` if appropriate
  - [ ] Adapt for predicate logic proposition handling

### Validator Integration
- [x] Update `runtime/validator.py`:
  - [x] Leverage `formalities.validation` for logical validation
  - [x] Use `formalities.validation.strategies` for checking steps
  - [x] Connect FALL validation to formalities validation pipeline

## Phase 5: Syntax and User Experience

### FALL Syntax Enhancements
- [ ] Add natural predicate logic syntax to FALL:
  - [ ] Support for quantifiers (∀, ∃)
  - [ ] Support for variables and constants
  - [ ] Simplified axiom definition using formalities constructs

### Shell Integration
- [ ] Update `runtime/shell.py`:
  - [ ] Add better error reporting for logical failures
  - [ ] Improve feedback on inference rule application
  - [ ] Add visualization of proof steps if possible

## Phase 6: Testing and Documentation

### Test Integration
- [x] Create test cases that use:
  - [x] Basic syllogisms from LogicAsker
  - [ ] Predicate logic examples from formalities tests
  - [x] NLP bridging with quantified statements

### Documentation
- [ ] Update docs to explain:
  - [ ] How FALL integrates with formalities
  - [ ] Available inference rules from formalities
  - [ ] Simplified syntax for common logical patterns

## Immediate First Steps
1. ✅ Map existing FALL constructs to their formalities counterparts
2. ✅ Create adapter between NLP bridge output and formalities types
3. ✅ Integrate formalities validation with FALL proof verification
4. ✅ Test simple syllogistic reasoning using formalities core rules
5. ⬜ Enhance FALL parser to support quantifiers and variables

This plan ensures we leverage the existing formalities framework rather than duplicating functionality, resulting in a more consistent and maintainable system.
