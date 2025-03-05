# VALIUM -- Numerical Statements Processing TODO

## Core Structure Enhancements
- [x] Update `formalities/fall/core/types/language/common.py`:
  - [x] Add `NUMERICAL` to `StatementType` enum
  - [x] Add numerical patterns to `PATTERNS.STATEMENTTYPES`
  - [x] Add numerical relationship types to `RelationshipType` enum
  - [x] Create numerical function types in `WordFunction` enum
  - [x] Add `NUMERICALCHECKS` to `PATTERNS`
  - [x] Add `NumberCheck` and `OperatorCheck` to `CheckFunctions`

## Base Language Capabilities
- [x] Update `formalities/fall/core/types/language/base.py`:
  - [x] Add numerical structure extraction method to `Statement` class (`_extractnumericalstructure()`)
  - [x] Enhance word tagging to handle numerical terms (updated `_determinetype()`)
  - [x] Add support for numerical relationships detection (updated `_determinerelationships()`)
  - [x] Implement numerical function assignment (added `_assignnumericalfunctions()`)
  - [x] Add numerical validation logic (added `validatenumerical()`)

## Numerical Processing Module
- [x] Create new file `formalities/fall/core/types/language/numerical.py`:
  - [x] Implement `NumericalStructureExtractor` class
    - [x] General extraction method for all numerical structures
    - [x] Specialized extraction methods for different numerical contexts
    - [x] Type identification for numerical statements (counting, arithmetic, etc.)
  - [x] Implement `NumericalStatement` class extending `Statement`
    - [x] Properties for numerical attributes (operands, operators, result)
    - [x] Methods for extracting relevant components
    - [x] Override `__post_init__` to handle numerical-specific initialization
  - [x] Implement base `NumericalValidator` class
    - [x] Abstract validation methods
    - [x] Strategy determination based on statement context

## Testing Infrastructure
- [ ] Create new file `sandbox/tests/fall/numerical_processing.py`:
  - [ ] Implement `test_numerical_statement_detection()`
  - [ ] Implement `test_counting_validation()`
  - [ ] Implement `test_arithmetic_validation()`
  - [ ] Implement `test_numerical_extraction()`
