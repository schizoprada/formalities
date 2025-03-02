# ~/formalities/src/formalities/fall/bridges/nlp.py
import re, typing as t
import spacy, nltk
from nltk.corpus import wordnet as wn
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
    commontokens: set[str] = field(default_factory=set)
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

    def tokenizedef(self, definition: t.Optional[str] = None) -> set:
        if not definition:
            return set()
        doc = self.nlp(definition.lower())
        return {token.lemma_ for token in doc if not token.is_stop and token.is_alpha and len(token.text) > 2}

    def getsimilarity(self, t1: str, t2: str) -> float:
        log.info(f"NLPBridge.getsimilarity | calculating similarity between terms: <{t1}> and <{t2}>")
        if (not t1) or (not t2):
            return 0.0
        t1 = t1.lower().strip()
        t2 = t2.lower().strip()

        if (t1==t2):
            return 1.0
        d1 = self.nlp(t1)
        d2 = self.nlp(t2)
        sim = d1.similarity(d2)
        log.info(f"NLPBridge.getimilarity | Similarity between <{t1}> and <{t2}>: {sim:.2f}")
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

    def validateinference(self, premises: t.List[Proposition], conclusion: Proposition) -> SemanticValidationResult:
            """
            Validate if a conclusion can be semantically inferred from the premises.
            """
            log.debug(f"NLPBridge.validateinference | Start validation for premises: {premises} | Conclusion: {conclusion}")
            if not self.enabled:
                log.warning("NLPBridge.validateinference | NLP Bridge disabled, returning default valid result.")
                return SemanticValidationResult(True, 1.0, [], reason="NLP Bridge disabled")

            # Extract texts from premises and conclusion
            premisetexts = [getattr(p, 'text', str(p)) for p in premises]
            conclusiontext = getattr(conclusion, 'text', str(conclusion))

            log.info(f"NLPBridge.validateinference | Extracting structures for premises: {premisetexts} | Conclusion: {conclusiontext}")

            # Get structures for analysis
            structures = []
            for text in (premisetexts + [conclusiontext]):
                struct = self.extractstructure(text)
                structures.append(struct)
                log.debug(f"Extracted structure for '{text}': {struct}")

            premisestructs = structures[:-1]
            conclusionstruct = structures[-1]

            connections = []

            # Check subject connection
            subjectmatches = []
            if conclusionstruct.subject:
                for i, pstruct in enumerate(premisestructs):
                    if pstruct.subject:
                        sim = self.getsimilarity(conclusionstruct.subject, pstruct.subject)
                        log.debug(f"Subject match check | Premise {i}: {pstruct.subject} | Conclusion: {conclusionstruct.subject} | Similarity: {sim}")
                        if sim >= self.simthresh:
                            subjectmatches.append((i, sim))
                        connections.append((f"subj-match-{i}", f"{conclusionstruct.subject}-{pstruct.subject}", sim))

            # Check predicate connection
            predicatematches = []
            conclusionpredicates = conclusionstruct.objects + list(conclusionstruct.modifiers.values())
            for i, pstruct in enumerate(premisestructs):
                premisepredicates = pstruct.objects + list(pstruct.modifiers.values())
                for cpred in conclusionpredicates:
                    for ppred in premisepredicates:
                        if cpred and ppred:
                            sim = self.getsimilarity(cpred, ppred)
                            log.debug(f"Predicate match check | Premise {i}: {ppred} | Conclusion: {cpred} | Similarity: {sim}")
                            connections.append((f"pred-match-{i}", f"{cpred}-{ppred}", sim))
                            if sim >= self.simthresh:
                                predicatematches.append((i, sim))

            # Token overlap calculation
            allcommontokens = set()
            overlapscores = []
            for cpred in conclusionpredicates:
                if not cpred:
                    continue
                for i, pstruct in enumerate(premisestructs):
                    premisepredicates = (pstruct.objects + list(pstruct.modifiers.values()))
                    for ppred in premisepredicates:
                        if not ppred:
                            continue
                        overlap, common = self.calctokenoverlap(cpred, ppred)
                        overlapscores.append((overlap, common))
                        allcommontokens.update(common)
                        connections.append((f"token-overlap-pred-{i}", f"{cpred}-{ppred}", overlap))
                        log.debug(f"Token Overlap | Premise {i}: {ppred} | Conclusion: {cpred} | Overlap Score: {overlap} | Common Tokens: {common}")

            bestoverlap = max([score for score, _ in overlapscores], default=0.0)

            existingvalid = (len(subjectmatches) > 0) and (len(predicatematches) > 0)
            overlapvalid = bestoverlap >= 0.2
            valid = existingvalid and bestoverlap >= 0.1

            confidence = 0.0
            if connections:
                confidence = (
                    (0.6 * (sum(sim for _, _, sim in connections) / len(connections))) +
                    (0.4 * bestoverlap)
                )

            if valid:
                commontokenstring = "; ".join(list(allcommontokens)[:5])
                reason = (
                    f"Valid inference found: {len(subjectmatches)} subject matches, "
                    f"{len(predicatematches)} predicate matches, "
                    f"Token Overlap Score: {bestoverlap:.2f}. "
                    f"Common Tokens: {commontokenstring if commontokenstring else 'None'}"
                )
            else:
                missing = []
                if not subjectmatches:
                    missing.append("Subject Connection")
                if not predicatematches:
                    missing.append("Predicate Connection")
                if not overlapvalid:
                    missing.append("Sufficient Token Overlap")
                reason = f"Invalid Inference - Missing: {', '.join(missing)}"

            result = SemanticValidationResult(valid, confidence, connections, allcommontokens, reason)
            log.info(f"NLPBridge.validateinference | Validation Completed | Result: {result}")
            return result

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

    def recursewordnet(self, term: str, maxdepth: int = 3, visited: t.Optional[set] = None) -> set:
        """
        Recursively explore WordNet for hypernyms of a term, extracting relevant tokens.
        """
        if visited is None:
            visited = set()

        log.debug(f"Starting recursewordnet | Term: {term} | Max Depth: {maxdepth}")
        tokens = set()
        synsets = wn.synsets(term)
        log.info(f"Found {len(synsets)} synsets for term '{term}'")

        for synset in synsets:
            if synset in visited:
                log.debug(f"Skipping already visited synset: {synset.name()}")
                continue
            visited.add(synset)

            definition = synset.definition()
            extracted_tokens = self.tokenizedef(definition)
            tokens.update(extracted_tokens)
            log.debug(f"Processing synset: {synset.name()} | Definition: {definition} | Extracted Tokens: {extracted_tokens}")

            if maxdepth > 0:
                for hypernym in synset.hypernyms():
                    hypernym_name = hypernym.name().split('.')[0]
                    log.info(f"Recursing into hypernym: {hypernym_name} | Remaining Depth: {maxdepth - 1}")
                    tokens.update(self.recursewordnet(hypernym_name, maxdepth - 1, visited))

        log.debug(f"Completed recursewordnet for term '{term}' | Extracted Tokens: {tokens}")
        return tokens


    def calctokenoverlap(self, t1: str, t2: str, maxdepth: int = 3) -> tuple[float, set]:
        log.debug(f"NLPBridge.calctokenoverlap | calculating overlap between tokens: <{t1}> and <{t2}> | max depth: {maxdepth}")
        tk1 = self.recursewordnet(t1, maxdepth)
        tk2 = self.recursewordnet(t2, maxdepth)

        if not tk1 or not tk2:
            return 0.0, set()

        intersection = tk1.intersection(tk2)
        union = tk1.union(tk2)

        overlap = (len(intersection) / len(union)) if union else 0.0
        log.info(f"NLPBridge.calctokenoverlap | <{t1}> and <{t2}> calculations -- overlap: {overlap} -- intersection: {intersection}")
        return overlap, intersection


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
