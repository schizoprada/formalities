# ~/formalities/src/formalities/fall/bridges/nlp.py
import re, typing as t
import spacy
from dataclasses import dataclass, field
from formalities.core.types.propositions import (
    Proposition, AtomicProposition, CompoundProposition, NumericProposition
)
from formalities.fall.utils.exceptions import ValidationException
from loguru import logger as log

@dataclass
class NLPToken:
    """A token from natural language processing."""
    text: str
    pos: str  # Part of speech
    lemma: str  # Base form
    index: int  # Position in sentence

@dataclass
class NLPEntity:
    """A named entity from natural language processing."""
    text: str
    type: str  # Entity type (PERSON, ORG, etc.)
    start: int
    end: int

@dataclass
class NLPStructure:
    """Structure extracted from natural language."""
    subject: t.Optional[str] = None
    verb: t.Optional[str] = None
    objects: t.List[str] = field(default_factory=list)
    modifiers: t.Dict[str, str] = field(default_factory=dict)

@dataclass
class SemanticValidationResult:
    """Result of a semantic validation."""
    valid: bool
    confidence: float = 0.0
    connections: t.List[t.Tuple[str, str, float]] = field(default_factory=list)
    reason: t.Optional[str] = None


class NLPBridge:
    def __init__(self, model: str = "en_core_web_md", fallbackmodel: str = "en_core_web_sm", simthresh: float = 0.65):
        """Initialize the NLP bridge."""
        self.enabled = False
        self.model = model
        self.fallbackmodel = fallbackmodel
        self.simthresh = simthresh
        self._nlp = None
        self._stemmer = None
        self.stopwords = {"the", "a", "an", "of", "or", "with", "and", "to", "in", "on", "by", "for", "at"} # this should probably be defined in a common components file

    @property
    def nlp(self):
        """Lazy-load spaCy model when needed."""
        if self._nlp is None:
            try:
                self._nlp = spacy.load(self.model)
                log.info(f"Loaded Spacy Model: {self.model}")
            except Exception as e:
                log.error(f"Failed To Load Spacy Model ({self.model}): {str(e)}")
                try:
                    self._nlp = spacy.load(self.fallbackmodel)
                    log.info(f"Loaded Fallback Spacy Model: {self.fallbackmodel}")
                except Exception as e:
                    log.error(f"Failed To Load Fallback Spacy Model ({self.fallbackmodel}): {str(e)}")
                    raise ValidationException(f"NLP Model could not be loaded: {str(e)}")
        return self._nlp

    def enable(self):
        self.enabled = True
        _ = self.nlp # force load when enabling
        return f"NLP Bridge Activated (Similarity Threshold: {self.simthresh:.2f})"

    def disable(self):
        self.enabled = False
        return "NLP Bridge Deactivated"

    def setsimthresh(self, threshold: float):
        if (0.0 <= threshold <= 1.0):
            self.simthresh = threshold
            return f"Similarity Threshold Set To: {threshold:.2f}"
        raise ValueError("Threshold must be between 0.0 and 1.0")

    def extractstructure(self, text: str) -> NLPStructure:
        log.info(f"NLPBridge.extractstructure | extracting structure from text:\n{text}")
        doc = self.nlp(text)
        structure = NLPStructure()

        if (subjects:=[token.text for token in doc if token.dep_ in ["nsubj", "nsubjpass"]]): # this should probably be defined in a common components file
            structure.subject = subjects[0]

        if (verbs:=[token.lemma_ for token in doc if token.pos_ == "VERB"]):
            structure.verb = verbs[0]

        objs = [token.text for token in doc if token.dep_ in ["dobj", "pobj", "attr"]] # this should probably be defined in a common components file
        structure.objects = objs
        for token in doc:
            if token.dep_ == "amod" and token.head.text in ([structure.subject] + structure.objects):
                structure.modifiers[token.head.text] = token.text
        log.info(f"NLPBridge.extractstructure | extracted structure: {structure}")
        return structure

    def tokenize(self, text: str) -> t.List[str]:
        if not text:
            return []
        doc = self.nlp(text)
        return [token.lemma_ for token in doc if not token.is_stop and token.is_alpha]

    def getsimilarity(self, t1: str, t2: str) -> float:
        if (not t1) or (not t2):
            return 0.0
        t1 = t1.lower().strip()
        t2 = t2.lower().strip()

        if (t1==t2):
            return 1.0
        d1 = self.nlp(t1)
        d2 = self.nlp(t2)
        sim = d1.similarity(d2)
        log.info(f"Similarity between '{t1}' and '{t2}': {sim:.2f}")
        return sim

    def validateterms(self, terms: t.List[t.Tuple[str, str]]) -> SemanticValidationResult:
        log.info(f"NLPBridge.validateterms | received terms: {terms}")
        connections = []
        validconnections = 0
        totalsimilarity = 0.0
        for t1, t2 in terms:
            sim = self.getsimilarity(t1, t2)
            connections.append((t1, t2, sim))

            if (sim >= self.simthresh):
                validconnections += 1
                totalsimilarity += sim

        avgsim = (totalsimilarity / len(terms)) if terms else 0.0
        valid = (validconnections >= len(terms) // 2)
        reason = f"Found {validconnections}/{len(terms)} valid semantic connections" if valid else f"Insufficient semantic connections ({validconnections}/{len(terms)})"
        result = SemanticValidationResult(
            valid=valid,
            confidence=avgsim,
            connections=connections,
            reason=reason
        )
        log.info(f"NLPBridge.validateterms | result: {result}")
        return result

    def validateinference(self, premises: t.List[t.Any], conclusion: t.Any) -> SemanticValidationResult:
        """
        Validate if a conclusion can be semantically inferred from the premises.
        """
        if not self.enabled:
            return SemanticValidationResult(True, 1.0, [], "NLP Bridge disabled")

        # Extract texts from premises and conclusion
        premisetexts = [getattr(p, 'text', str(p)) for p in premises]
        conclusiontext = getattr(conclusion, 'text', str(conclusion))

        log.info(f"Validating inference from {premisetexts} to {conclusiontext}")

        # Get structures for analysis
        structures = []
        for text in premisetexts + [conclusiontext]:
            struct = self.extractstructure(text)
            structures.append(struct)

        premisestructs = structures[:-1]
        conclusionstruct = structures[-1]

        # For syllogistic reasoning, we need to check:
        # 1. Subject of conclusion matches a subject in premises
        # 2. Predicate of conclusion matches a predicate in premises
        # 3. There's a "bridge" term connecting premises

        # Check subject connection (conclusion subject should match a premise subject)
        subjectmatches = []
        if conclusionstruct.subject:
            for i, pstruct in enumerate(premisestructs):
                if pstruct.subject:
                    sim = self.getsimilarity(conclusionstruct.subject, pstruct.subject)
                    if sim >= self.simthresh:
                        subjectmatches.append((i, sim))

        # Check predicate connection (conclusion predicate should match a premise predicate)
        predicatematches = []
        conclusionpredicates = conclusionstruct.objects + list(conclusionstruct.modifiers.values())
        for i, pstruct in enumerate(premisestructs):
            premisepredicates = pstruct.objects + list(pstruct.modifiers.values())
            for c_pred in conclusionpredicates:
                for p_pred in premisepredicates:
                    if c_pred and p_pred:
                        sim = self.getsimilarity(c_pred, p_pred)
                        if sim >= self.simthresh:
                            predicatematches.append((i, sim))

        # Check for bridge terms between premises
        bridgeterms = []
        if len(premisestructs) >= 2:
            for i, p1 in enumerate(premisestructs):
                for j in range(i+1, len(premisestructs)):
                    p2 = premisestructs[j]
                    # Check subject-subject connection
                    if p1.subject and p2.subject:
                        sim = self.getsimilarity(p1.subject, p2.subject)
                        if sim >= self.simthresh:
                            bridgeterms.append(("subject", i, j, sim))

                    # Check subject-predicate connections
                    p1predicates = p1.objects + list(p1.modifiers.values())
                    p2predicates = p2.objects + list(p2.modifiers.values())

                    if p1.subject:
                        for p2_pred in p2predicates:
                            if p2_pred:
                                sim = self.getsimilarity(p1.subject, p2_pred)
                                if sim >= self.simthresh:
                                    bridgeterms.append(("subj-pred", i, j, sim))

                    if p2.subject:
                        for p1_pred in p1predicates:
                            if p1_pred:
                                sim = self.getsimilarity(p2.subject, p1_pred)
                                if sim >= self.simthresh:
                                    bridgeterms.append(("pred-subj", i, j, sim))

        # Collect all semantic connections
        connections = [
            (f"subject-match-{i}", f"{conclusionstruct.subject}-{premisestructs[i].subject}", sim)
            for i, sim in subjectmatches
        ] + [
            (f"predicate-match-{i}", "predicate-similarity", sim)
            for i, sim in predicatematches
        ] + [
            (f"bridge-{i}-{j}", bridge_type, sim)
            for bridge_type, i, j, sim in bridgeterms
        ]

        # For a valid syllogism, we need:
        # 1. At least one subject match
        # 2. At least one predicate match
        # 3. At least one bridge term (for multiple premises)
        valid = len(subjectmatches) > 0 and len(predicatematches) > 0

        if len(premises) >= 2:
            valid = valid and len(bridgeterms) > 0

        confidence = sum(sim for _, _, sim in connections) / len(connections) if connections else 0.0

        if valid:
            reason = "Valid semantic inference path found"
        else:
            missing = []
            if not subjectmatches:
                missing.append("subject connection")
            if not predicatematches:
                missing.append("predicate connection")
            if len(premises) >= 2 and not bridgeterms:
                missing.append("bridge term between premises")
            reason = f"Invalid inference: missing {', '.join(missing)}"

        log.info(f"Validation result: {valid} (confidence: {confidence:.2f})")
        log.info(f"Reason: {reason}")

        return SemanticValidationResult(valid, confidence, connections, reason)

    def symbolize(self, proposition):
        """Generate symbolic representation of a proposition."""
        if not self.enabled:
            return f"Symbol({getattr(proposition, 'text', str(proposition))})"

        text = getattr(proposition, 'text', str(proposition))
        structure = getattr(proposition, 'structure', {})

        # If we have structure information, use it
        if structure:
            subject = structure.get('SUBJECT', '')
            predicate = structure.get('PREDICATE', '')

            if subject and predicate:
                return f"{predicate.capitalize()}({subject.capitalize()})"

        # Otherwise parse with spaCy
        doc = self.nlp(text)

        # Find main predicate and its arguments
        predicate = None
        arguments = []

        for token in doc:
            if token.dep_ == "ROOT" and token.pos_ in ["VERB", "ADJ"]:
                predicate = token.lemma_

            if token.dep_ in ["nsubj", "dobj", "pobj", "attr"]:
                arguments.append((token.i, token.text, token.dep_))

        # Sort arguments by position in sentence
        arguments.sort()

        if predicate and arguments:
            argstext = ", ".join(arg[1].capitalize() for arg in arguments)
            return f"{predicate.capitalize()}({argstext})"

        # Fallback - just wrap the text
        return f"Prop({text})"

    def extractquantifier(self, text:str) -> t.Optional[str]:
        """
        Extract quantifier information from text.
        Returns:
            "universal" for ["all", "every", etc.]
            "existential" for ["some", "there exists", etc.]
            None if no quantifier found
        """
        # simple pattern matching for now, to be expanded
        text = text.lower()
        if any(q in text for q in ["all", "every", "each"]):
            return "universal"
        elif any(q in text for q in ["some", "there exists", "there is a "]):
            return "existential"
        return None

    def toformalitiesproposition(self, text: str, name: str) -> Proposition:
        """
        Convert natural language text to a formalities proposition.
        Uses NLP to extract logical structure.

        Args:
            text: Natural language text
            name: Name for the resulting proposition

        Returns:
            Formalities proposition representing the text
        """
        structure = self.extractstructure(text)

        if (quantifier:=self.extractquantifier(text)) == "universal":
            # Handle universal statements like "All men are mortal"
            # Creates a formalities universal proposition
            # This is a placeholder - we'll need to implement proper conversion
            subjclass = structure.subject
            predicate = structure.objects[0] if structure.objects else None
            # Using formalities to create a proposition that represents "∀x(Subject(x) → Predicate(x))"
            # This will need to be refined based on formalities' predicate logic support
            return AtomicProposition(name, _truthvalue=None)
        # Handle simple statements like "Socrates is a man"
        if (structure.subject and structure.objects):
            # Creates a simple atomic proposition
            return AtomicProposition(name, _truthvalue=None)

        # Default Case
        return AtomicProposition(name, _truthvalue=None)

'''
class NLPBridge:
    """Bridge for natural language processing in FALL."""

    def __init__(self):
        """Initialize the NLP bridge."""
        # Basic patterns for extracting structure
        self.patterns = {
            "subjectverb": re.compile(r"(?P<subject>\w+)\s+(?P<verb>\w+)"),
            "subjectverbobject": re.compile(r"(?P<subject>\w+)\s+(?P<verb>\w+)\s+(?P<object>\w+)"),
            "subjectisobject": re.compile(r"(?P<subject>\w+)\s+is\s+(?P<object>\w+)"),
        }

    def extractstructure(self, text: str) -> NLPStructure:
        """Extract basic structure from natural language text."""
        # Very simplified extraction - in a real system, use a proper NLP library
        structure = NLPStructure()

        # Try each pattern
        for patternname, pattern in self.patterns.items():
            match = pattern.search(text)
            if match:
                if 'subject' in match.groupdict():
                    structure.subject = match.group('subject')
                if 'verb' in match.groupdict():
                    structure.verb = match.group('verb')
                if 'object' in match.groupdict():
                    structure.objects.append(match.group('object'))

        # Extract modifiers based on common patterns
        adjpattern = re.compile(r"(?P<adj>\w+)\s+(?P<noun>\w+)")
        for match in adjpattern.finditer(text):
            if match.group('noun') == structure.subject:
                structure.modifiers[match.group('noun')] = match.group('adj')
            elif match.group('noun') in structure.objects:
                structure.modifiers[match.group('noun')] = match.group('adj')

        return structure

    def texttoassertion(self, text: str) -> str:
        """Convert natural language to a logical assertion."""
        structure = self.extractstructure(text)

        # Very simple conversion based on common patterns
        if structure.subject and structure.verb == "is" and structure.objects:
            return f"{structure.subject} IS {structure.objects[0]}"
        elif structure.subject and structure.verb and structure.objects:
            return f"{structure.subject} {structure.verb.upper()} {structure.objects[0]}"
        elif structure.subject and structure.verb:
            return f"{structure.subject} {structure.verb.upper()}"
        else:
            # Default to treating the text as a literal proposition
            return text

    def identifycontradictions(self, texts: t.List[str]) -> t.List[t.Tuple[str, str, str]]:
        """Identify potential contradictions between natural language statements."""
        contradictions = []
        assertions = [self.texttoassertion(text) for text in texts]

        # Very simplified contradiction detection
        for i, assertion1 in enumerate(assertions):
            for j, assertion2 in enumerate(assertions):
                if i >= j:
                    continue

                # Check for simple contradictions like "X is Y" and "X is not Y"
                if "NOT" in assertion1 and assertion1.replace("NOT", "") == assertion2:
                    contradictions.append((texts[i], texts[j], "direct negation"))
                elif "NOT" in assertion2 and assertion2.replace("NOT", "") == assertion1:
                    contradictions.append((texts[i], texts[j], "direct negation"))

        return contradictions

    def simplify(self, text: str) -> str:
        """Simplify natural language to core logical meaning."""
        # Remove filler words and normalize structure
        fillers = ["the", "a", "an", "that", "very", "quite", "just"]
        simplified = text.lower()

        for filler in fillers:
            simplified = re.sub(fr'\b{filler}\b', '', simplified)

        # Normalize whitespace
        simplified = re.sub(r'\s+', ' ', simplified).strip()

        return simplified
'''
