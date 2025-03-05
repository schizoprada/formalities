# FALL - TODO - Mar. 2nd, 2025

## NLP Bridge Enhancement (Iterative Process)

1. **Fix Semantic Relationship Detection**
   - [ ] **Hypothesis 1: Universal Statement Extraction**
     - [ ] Create sandbox script to test universal statement pattern recognition
     - [ ] Evaluate pattern recognition success rates
     - [ ] Refine pattern matching approach based on results

   - [ ] **Hypothesis 2: Term Relationship Detection**
     - [ ] Test multiple relationship detection methods in sandbox
     - [ ] Compare Wu-Palmer vs. path-based vs. custom syntactic approaches
     - [ ] Select best performing approach(es) based on results

   - [ ] **Hypothesis 3: Traversal Approach for Indirect Relationships**
     - [ ] Test controlled depth traversal in WordNet
     - [ ] Develop scoring mechanism that accounts for traversal distance
     - [ ] Evaluate performance on indirect relationships

2. **Inference Validation Integration**
   - [ ] **Hypothesis: Multi-metric Validation**
     - [ ] Test combined approach using multiple relationship metrics
     - [ ] Determine optimal weighting for different relationship types
     - [ ] Validate against test syllogisms before integration

3. **Integration Strategy**
   - [ ] Integrate only proven approaches into NLP Bridge
   - [ ] Update validateinference() with best performing methods
   - [ ] Update ProofExecutor with integrated validation approach

4. **Final Testing**
   - [ ] Run comprehensive tests with both valid and invalid syllogisms
   - [ ] Fine-tune thresholds based on test results
   - [ ] Document findings and approach



# GOAL
given a statement such as :
```txt
Socrates is a man.
All men are mortal.
Socrates is mortal
```

which is comprised of the following propositions:
1. Socrates is a man.
2. All men are mortal.
3. Socrates is mortal

our processing pipeline should break it down as follows:
1. "Socrates is a man"
  - identify `"Socrates"` as the subject noun
  - identify `"man"` as the predicate nominative
  - identify `"is (a)"` as the linking verb, more specifcally a copula
  - identify that the composition of the statement makes it one of:
    (Particular, Declarative, Factual, etc.)
    > possibly even identify the proper type of statement
  - without knowing who socrates is, or what a man is,
    it should be able to identify that the statement is establishing
    a hypernimic relationship from the predicate nominative
    to the subject noun by means of a copulative linking verb
    aka its declaring an identity/equivalence relationship

2. "All men are mortal"
  - identify `"All"` as a universal quantifier
  - identify `"men"` as the subject noun
  - identify `"mortal"` as the predicate adjective
  - identify `"are"` as the copulative linking verb
  - use the composition to identify the statement as
    a (universal, declarative, factual) statement
  - without knowing what men are, or what mortality is,
    it should be able to identify that the statement is establishing a
    characteristic relationship from the predicative property
    to the subject noun, by means of a copulative linking verb
    via the universal quantifier
    aka its declaring a universal characteristic relationship

3. "Socrates is mortal"
  - identify `"Socrates"` as the subject noun
  - identify `"mortal"` as the predicate adjective
  - idenify `"is"` as the couplative linking verb
  - use the composition to identify the statement as
  - without knowing who Socrates is, or what mortality is,
  it should be able to identify that the statement is establishing
  a characteristic relationship between the subject noun
  and the predicate adjective, by means of a copulative linking verb.
  Aka, it’s declaring that Socrates possesses the property of
  mortality ), and the sentence is not establishing an
  equivalence or identity relationship,
  but rather assigning a characteristic to the subject.

4. Atomic Reduction
  a. "Socrates is a man"
   - `is a` implies the atomicity of both `Socrates` and `man`
   - hence we know that `man` is atomic
  b. "All men are mortal"
   - `All` implies a universal quantization of the following subject noun
      which happens to be `men`
   - use NLP to establish that `man` is the atomic singular of `men`
  c. "Socrates is mortal"
   - `is` implies the atomicity of`Socrates`
      although this may be unnecessary, given that
      the atomicity of `Socrates` has already been established

5. Syntactic Evaluation
  a. "Socrates is a man"
   - knowing that this is an identical/equivalent relationship statement
     due to the copulative linking verb
   - knowing that `Socrates` is an atomic subject noun
   - knowing that `man` is an atomic predicate nominative
   - establish the identity of socrates as an instance of man
   > e.g. `Socrates(Man(name='Socrates'))`
  b. "All men are mortal"
   - use the implication of universal quantization to deduce that
     the characteristic of `mortal` applies to each instance of `men`
     which has been atomized to `man`, hence `mortal` applies to `man`
   > e.g. `Man.mortal == True # True`

6. Semantic Evaluation
  c. "Socrates is mortal"
  > e.g.
  ```py
  @dataclass
  class Man:
    name: str # established from statement 1
    mortal: bool = True # established from statement 2

  Socrates = Man(name="Socrates")
  Socrates.mortal # True
  ```


## ANALYSIS
