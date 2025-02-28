# CHANGELOG

## [0.0.1] - February 20th, 2025

  ### Added

  #### Core Types
  - Established base type system with `LogicType` enum
  - Created generic `Registry` system for type-safe instance management
  - Implemented `Atomic` base class for indivisible logical elements
  - Created `Compound` base class for composite logical structures

  #### Propositions
  - Implemented `Proposition` abstract base class
  - Created `AtomicProposition` combining `Atomic` and `Proposition`
  - Implemented `CompoundProposition` combining `Compound` and `Proposition`
  - Added support for proposition evaluation with context

  #### Operators
  - Created base `Operator` class with arity validation
  - Implemented operator hierarchy (Unary, Binary, N-ary)
  - Added core boolean operators:
    - Basic: AND, OR, NOT, IMPLIES
    - Complex: XOR, NAND, NOR, IFF/XNOR
    - N-ary versions: AND_N, OR_N, NAND_N, NOR_N

  #### Frameworks
  - Created `Framework` abstract base class
  - Implemented `ValidationResult` for framework validation
  - Added `ClassicalFramework` with:
    - Law of excluded middle enforcement
    - Contradiction detection
    - Operator compatibility checking

  #### Validation
  - Established validation type system with `ValidationType` enum
  - Created `ValidationStrategy` pattern
  - Implemented core validation strategies:
    - Syntactic validation
    - Logical consistency checking
  - Added `Validator` class for strategy orchestration

  ### Project Structure
  ```
  src/formalities/
  ├── core/
  │   └── types/
  │       ├── atomic.py
  │       ├── compound.py
  │       ├── logic.py
  │       ├── registry.py
  │       ├── operators/
  │       │   ├── base.py
  │       │   └── boolean.py
  │       └── propositions/
  │           ├── base.py
  │           ├── atomic.py
  │           └── compound.py
  ├── frameworks/
  │   ├── base.py
  │   └── simple.py
  └── validation/
      ├── base.py
      └── strategies/
          ├── syntactic.py
          └── logicalconsistency.py
  ```

  ### Documentation
  - Created initial project abstract
  - Established core architectural principles
  - Defined base class hierarchies and relationships

  ### Notes
  - All core components maintain type safety through typing hints
  - Systems designed for extensibility and future enhancement
  - Framework validates against basic logical principles
  - Basic validation pipeline established

  ### TODO
  - Implement additional frameworks (Modal, Intuitionistic)
  - Add more validation strategies
  - Create test suite
  - Add documentation strings to all modules
  - Implement more complex operators

## [0.0.2] - February 20th, 2025
  ### Added

  #### Tool Integration System
  - Created `ToolCallHandler` for managing LLM tool calls
  - Implemented standardized `ToolCallRequest` and `ToolCallResponse` types
  - Added `matchmaker` tool for framework component discovery
  - Added `methodbuilder` tool for dynamic code execution and validation
  - Integrated logging system using loguru

  #### Framework Discovery
  - Implemented `FrameworkRegistry` for automatic component discovery
  - Created `ComponentInfo` dataclass for component metadata
  - Added recursive directory scanning for framework components
  - Implemented flexible component querying system
  - Added automatic registration of frameworks, validators, and operators

  #### Integration & Utilities
  - Added global instances for immediate use (`frameworkregistry`, `toolcallhandler`)
  - Implemented safe module importing and class loading
  - Added error handling and logging throughout
  - Created type-safe interfaces for tool interactions

  ### Enhanced
  - Added logging throughout the codebase
  - Improved error handling and reporting
  - Streamlined component registration process

  ### Architecture
  - Established utility module structure
  - Created clean separation between discovery and tool call systems
  - Implemented singleton pattern for global handlers

  ### TODO
  - Add sandboxing for code execution in methodbuilder
  - Implement caching system for frequently used components
  - Create comprehensive test suite for tool calls
  - Add validation context support to methodbuilder
  - Enhance matchmaker query capabilities with fuzzy matching
  - Add support for async tool calls
  - Create interface documentation for LLM integration
  - Add version compatibility checking
  - Implement component dependency resolution
  - Add support for custom tool registration
  - Create examples of LLM interactions
  - Add metrics collection for tool usage
  - Create cleanup mechanisms for temporary resources
  - Add type checking for methodbuilder args

## [0.0.3] - February 21st, 2025
  - added code formatting
  - added tool call arg validation
  - enhanced `ToolCallHandler._matchmaker` method return with import paths
  - completed unit testing
  ### 1.1 Numeric-Logic Bridge
  - [x] Create `NumericProposition` class
    - [x] Implement conversion from numeric computations to logical propositions
    - [x] Add to proposition type registry
    - [x] Implement comparison operations
    - [x] Add validation support

  ### 1.2 Type System Enhancements
  - [x] Create input/output type handling system
    - [x] Parameter type validation for methodbuilder
    - [x] Type conversion utilities (primitive → logical types)
    - [x] Result type handling

  ### 1.3 Validation Context
  - [x] Enhance ValidationContext implementation
    - [x] Add context passing in methodbuilder
    - [x] Implement framework-specific context handlers
    - [x] Add validation pipeline context support

  ### 1.4 Framework Selection
  - [x] Create framework selection utilities
    - [x] Add framework compatibility checking
    - [x] Implement framework constraint validation
    - [x] Add framework suggestion system

  ## 2. Unit Testing

  ### 2.1 Core Types
  - [x] Test NumericProposition
    - [x] Basic creation and comparison
    - [x] Numeric operations
    - [x] Type conversions
    - [x] Validation

  ### 2.2 Tool Handlers
  - [x] Test matchmaker
    - [x] Component discovery
    - [x] Query matching
    - [x] Response formatting
  - [x] Test methodbuilder
    - [x] Code execution
    - [x] Framework integration
    - [x] Error handling
    - [x] Context passing

  ### 2.3 Validation
  - [x] Test validation pipelines
    - [x] Context handling
    - [x] Framework validation
    - [x] Strategy execution
  - [x] Test type conversion
    - [x] Input validation
    - [x] Output handling
    - [x] Error cases


[0.0.7]
  *shiiiiiiiieet we skipped a couple versions its wtvr tho*
