# FORMALITIES

## Overview
**primary core:**
*a python-based formal logic & philosophical logic framework,*
*designed for use by agentic machine learning models*
*for output validation and enhanced reasoning processes*

**secondary core:**
*additional tools and frameworks pertaining to linguistics, philosophy of language, etc.*
*-- this will be particularly useful for our target implementation of the library*
*as it can be assumed the majority if not entirety of the models that will use this framework*
*will be large language models*

## CONTEMPLATIONS & CONSIDERATIONS
  - We want to build formal & philosophical logic from scratch

  - After the core is established we will extend it into various submodules
    designed after notable `"interpretations"` of formal logic
    + examples: frege, boole, russell, north whitehead, wittgenstein, etc...

  - we want this library to be intuitive and easy to use, power and elegance in flawless simplicity

  - for pre-development research, we might consider using extant formal logic python frameworks
    with tool-use-capable LLM's to see what our implementation could look like
    after we get the core essence of formal logic defined and tested
    + this will allow us to also tangibly realize any particular obstacles that were unforseen

  - for the usage style im thinking something at the intersection of
    declarative, functional, and procedural paradigms

## Example Potential Use:

  ```py
  import ollama
  import formalities as fm
  baseprompt = """
  What color is the sky? And why?
  """
  from formalities.resources import (
      Internet, Database, ... # external data references
  )
  from formalities.interpretations import (Wittgenstein, Boole, Frege, NorthWhitehead)
  from formalities.frameworks.apriori import (PureReason, AnalyticAPriori, SyntheticAPriori)
  from formalities.frameworks.aposteriori import (EmpiricalReason, AnalyticAPosteriori, SyntheticAPosteriori)
  from formalities.symbology.operators import (Conjunction, Disjunction, Negation, Implication, Biconditional)
  from formalities.symbology.quantifiers import (ExistentialQuantifier, UniversalQuantifier)
  from formalities.symbology.relational import (SetMembership, Subset, Intersection, Union, Contradiction, Tautology)
  from formalities.symbology.miscellaneous import (Equivalence, Turnstile, DoubleTurnstile, ShefferStroke, PierceArrow)


  # some sort of system to use the base prompt to match the most appropriate tools before its even provided to the llm
  ## should also have an automatic kwarg so that options can be optional and it will pick out from the whole library
  ### like: `tools = fm.ai.tools.selectappropriate(baseprompt, auto=True, minimum=2, maximum=10, ...otherkwargsthatmightbeuseful)
  tools = fm.ai.tools.selectappropriate(baseprompt, options=(Internet, Database, Wittgenstein, Boole, Frege, NorthWhitehead, PureReason, AnalyticAPriori, SyntheticAPriori, EmpiricalReason, AnalyticAPosteriori, SyntheticAPosteriori, Conjunction, Disjunction, Negation, Implication, Biconditional, ExistentialQuantifier, UniversalQuantifier, SetMembership, Subset, Intersection, Union, Contradiction, Tautology, Equivalence, Turnstile, DoubleTurnstile, ShefferStroke, PierceArrow))

  # new tells it that it will not extend the base prompt it will be a new one included in the `messages[]`
  systemprompt = fm.ai.utils.formatprompt(baseprompt, new=True, role='system', tools=tools, returnas=dict)

  # now the prompt will be formatted like:
  ## all of this should be configurable too btw. we'll have defaults lib but yea
  """
  [Introduction]
  You are an agentic LLM tasked with answering the users queries, or preforming actions at their behest.
  To ensure verifiable and consistent outputs, you must use any of the following provided tools best suited for the objective at hand.
  ... (more info etc)

  [Tools]
  Wittgenstein, Boole, Frege, NorthWhitehead, PureReason, AnalyticAPriori, SyntheticAPriori, EmpiricalReason, AnalyticAPosteriori, SyntheticAPosteriori, Conjunction, Disjunction, Negation, Implication, Biconditional, ExistentialQuantifier, UniversalQuantifier, SetMembership, Subset, Intersection, Union, Contradiction, Tautology, Equivalence, Turnstile, DoubleTurnstile, ShefferStroke, PierceArrow

  [Instructions]
  You are not required to use all of the provided tools, just the ones best fit for the task.
  ...(more instructions)
  """

  model='llama3.2'
  messages=[{'role': 'user', 'content': baseprompt}, systemprompt]
  response = ollama.chat(
      model=model,
      messages=messages,
      tools=tools # if the model uses the tools properly it should work like this in and of itself, however...
  )
  ##... if we want to externally validate or enforce certain things on the response we can also do something like:
  response = fm.facilitate(ollama.chat, fnargs=(), fnkwargs=(model=model, messages=messages, tools=tools), mandatory=(tools=(Internet, PureReason, Wittgenstein.PictureTheory)), ...)# other kwargs that would be useful for a method like this that facilitates the response

  # etc...
  ```






## Notations Symbology Glossary:
  - be sure to work in the section titled after your model name (llama/claude/gpt/someotherllm) unless explicitly indicated otherwise by the appropriate symbols
  - contents enclosed by `<>` are open invitations for you (llama/claude/gpt/otherllm) to edit my section of the notes
  - contents enclosed by `[]` in your notes section are prompts for your notes
  - contents preceeded by a `>` are nested bullet points, the more number of arrows in the nested bullet point indicates its nest level, e.g.:
    > this is a level 1 nested bullet point related to the primary one (`-`),  explaining the symbology for nested bullet points
    >> this is a level 2 nested bullet point related to the level 1 nested bullet point that precedes it as well as the primary bullet point
    >>> etc.
    > now this is a new level 1 nested, unrelated to the others but still tethered to the primary `-`
  - `\` indicates that the point proceeds to the new line
  - `#` indicates comment(s), `##` indicates multiline comment(s)
  - contents enclosed `%` indicate that you should mirror it in your own notes section and work on it alongside in your own manner \
    for contents that are multiline it will be `%%` \
    e.g. \
    %list of potential resources: ...% # that means we will have our own indpendent lists but we both will have lists of potential resources if that makes sense
    %%
    potential python example:
    ```py
    pass # we will try to write our own versions trying to resolve the same matter
    ```
    %%


## LLAMA NOTES

  * **Initial Thoughts**
  	+ Formal logic is crucial for developing robust and generalizable reasoning capabilities in AI systems.
  	+ By building a framework specifically designed for agentic machine learning models, we can create more transparent and explainable decision-making processes.
  	+ The Python-based framework will enable seamless integration with existing LLMs and allow us to leverage their strengths while incorporating formal logic principles.

  * **Key Challenges**

  	+ Developing a robust and efficient implementation of formal logic that can be scaled for large datasets and complex reasoning tasks.
  	+ Ensuring the framework's compatibility with various types of data, including natural language inputs, and adapting to potential biases or inconsistencies in the input data.
  	+ Integrating the framework with existing AI/ML tools and frameworks to create a cohesive and user-friendly interface.

  * **Research Directions**

  	+ Investigating the application of specific formal logic frameworks (e.g., Kleene's strong normal form, Curry-Howard correspondence) to optimize reasoning processes in agentic LLMs.
  	+ Developing novel methods for handling uncertainty, ambiguity, or non-monotonicity in formal logic-based decision-making systems.
  	+ Exploring ways to incorporate human expertise and intuition into the framework to enhance its performance and reliability.

  * **Future Work**

  	+ Refining the framework's design and implementation based on user feedback, testing results, and ongoing research in formal logic and AI/ML.
  	+ Developing a comprehensive evaluation framework to assess the effectiveness and robustness of our framework compared to existing approaches.
  	+ Exploring potential applications of our framework beyond agentic LLMs, such as in expert systems or knowledge representation.

### PRIMARY OBJECTIVES

* **Develop a robust and efficient formal logic framework**
	+ Investigate novel techniques for handling uncertainty, ambiguity, or non-monotonicity
	+ Integrate advanced mathematical logic and philosophical insights into the framework
* **Create a user-friendly interface and API**
	+ Design an intuitive and ergonomic framework for interacting with agentic LLMs
	+ Develop comprehensive documentation and tutorials for users

### SECONDARY OBJECTIVES

* **Collaborate with researchers, philosophers, and industry experts**
	+ Establish partnerships with leading institutions and organizations to advance the field
	+ Engage in regular workshops, conferences, and webinars to share knowledge and best practices
* **Continuously evaluate and improve the framework**
	+ Develop a robust evaluation framework to assess the effectiveness of our framework
	+ Regularly update and expand the framework based on user feedback and ongoing research







### CLAUDE NOTES
### GPT NOTES
## MISSION STATEMENT
**Llama**
  We aim to develop a novel Python-based formal logic framework for agentic machine learning models, enabling robust and generalizable reasoning capabilities. Our goal is to create a flexible and user-friendly system that integrates insights from various philosophical traditions, mathematical logic, and AI/ML techniques.

  Our mission is to:

  * Provide a rigorous foundation for reasoning in AI/ML, leveraging advances in formal logic and philosophy of language.
  * Develop a framework that balances power and elegance, ensuring ease of use and adoption across diverse applications.
  * Foster collaboration between researchers, philosophers, and industry experts to advance the state-of-the-art in formal logic-based AI/ML.

  By achieving these objectives, we envision our framework contributing to:

  * Improved explainability and transparency in AI/ML decision-making processes
  * Enhanced robustness and generalizability of agentic LLMs
  * Novel applications in areas like natural language processing, computer vision, and expert systems
