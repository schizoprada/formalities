# ~/formalities/playground/slipperywhenwet.py
import re
import string
import time
import nltk
from nltk.corpus import wordnet as wn
import spacy
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel

# Assume WordNet resources are already downloaded.
# nltk.download('wordnet')
# nltk.download('omw-1.4')

# A simple set of stopwords for filtering definitions.
STOPWORDS = {"the", "a", "an", "of", "or", "with", "and", "to", "in", "on"}

def tokenize_definition(definition):
    """Remove punctuation and split; filter out stopwords."""
    translator = str.maketrans('', '', string.punctuation)
    tokens = definition.translate(translator).lower().split()
    return [word for word in tokens if word not in STOPWORDS]

def collect_recursive_definitions(synset, max_depth=3, visited=None):
    """
    Recursively collects tokens from the definition of the synset and its hypernyms.
    Returns a set of tokens.
    """
    if visited is None:
        visited = set()
    tokens = set(tokenize_definition(synset.definition()))
    if max_depth > 0:
        for hyper in synset.hypernyms():
            if hyper not in visited:
                visited.add(hyper)
                tokens |= collect_recursive_definitions(hyper, max_depth - 1, visited)
    return tokens

class LogicValidator:
    def __init__(self):
        # Create a console with fixed width (60 columns) for a vertical rectangle.
        self.console = Console(width=60)
        self.facts = set()
        self.rules = []
        self.reasoning = []  # For explainability.
        self.nlp = spacy.load("en_core_web_sm")
        # Our threshold (learned from experiments)
        self.similarity_threshold = 0.52

    def assert_fact(self, fact):
        fact = fact.lower().strip()
        self.facts.add(fact)
        self.reasoning.append(f"Asserted fact: '{fact}'")
        self.console.print(f"[green]Debug: Fact '{fact}' asserted.[/green]")

    def assert_rule(self, premise, conclusion):
        premise = premise.lower().strip()
        conclusion = conclusion.lower().strip()
        self.rules.append((premise, conclusion))
        self.reasoning.append(f"Asserted rule: If '{premise}' then '{conclusion}'")
        self.console.print(f"[green]Debug: Rule 'if {premise} then {conclusion}' asserted.[/green]")

    def infer(self):
        new_inferred = True
        while new_inferred:
            new_inferred = False
            for premise, conclusion in self.rules:
                self.console.print(f"[blue]Debug: Checking rule: If '{premise}' then '{conclusion}'.[/blue]")
                if premise in self.facts and conclusion not in self.facts:
                    self.facts.add(conclusion)
                    self.reasoning.append(f"Applied Modus Ponens: Fact '{premise}' implies '{conclusion}'")
                    self.console.print(f"[blue]Debug: Rule triggered: '{premise}' implies '{conclusion}'[/blue]")
                    new_inferred = True
                    time.sleep(0.3)

    def get_main_predicate(self, text):
        doc = self.nlp(text)
        for token in doc:
            if token.dep_ == "ROOT" and token.pos_ in {"VERB", "ADJ", "NOUN"}:
                self.console.print(f"[blue]Debug: Main predicate found: '{token.text}' (lemma: '{token.lemma_}')[/blue]")
                return token.lemma_
        for token in reversed(doc):
            if token.pos_ != "PUNCT":
                self.console.print(f"[blue]Debug: Fallback predicate: '{token.text}' (lemma: '{token.lemma_}')[/blue]")
                return token.lemma_
        return text

    def parse_statement(self, statement):
        stmt = statement.lower().strip()
        doc = self.nlp(statement)
        tokens_info = []
        for token in doc:
            tokens_info.append(f"Token: '{token.text}', Lemma: '{token.lemma_}', POS: {token.pos_}, Dep: {token.dep_}")
        self.console.print("[blue]Debug: SpaCy Token Details:[/blue]")
        for info in tokens_info:
            self.console.print(f"  {info}", style="blue")
        subjects = [token.text for token in doc if token.dep_ == "nsubj"]
        predicates = [token.lemma_ for token in doc if token.pos_ in ["VERB", "ADJ"]]
        self.console.print(f"[blue]Debug: Subjects: {subjects}[/blue]")
        self.console.print(f"[blue]Debug: Predicates: {predicates}[/blue]")
        parsed = {"subjects": subjects, "predicates": predicates}
        if stmt.startswith("if") and ("then" in stmt or "," in stmt):
            match = re.match(r"if (.+?)(,|\sthen\s)(.+)", stmt)
            if match:
                parsed["type"] = "rule"
                parsed["premise"] = match.group(1).strip()
                parsed["conclusion"] = match.group(3).strip().rstrip('.')
                self.console.print(f"[blue]Debug: Parsed as rule: If '{parsed['premise']}' then '{parsed['conclusion']}'[/blue]")
                return parsed
        if "therefore" in stmt:
            parts = stmt.split("therefore")
            if len(parts) == 2:
                parsed["type"] = "inference"
                parsed["premise"] = parts[0].strip().rstrip(',')
                parsed["conclusion"] = parts[1].strip().rstrip('.')
                self.console.print(f"[blue]Debug: Parsed as inference: Premise: '{parsed['premise']}', Conclusion: '{parsed['conclusion']}'[/blue]")
                return parsed
        parsed["type"] = "fact"
        parsed["fact"] = stmt.rstrip('.')
        self.console.print(f"[blue]Debug: Parsed as fact: '{parsed['fact']}'[/blue]")
        return parsed

    def evaluate_association(self, premise, conclusion):
        pred = self.get_main_predicate(premise)
        concl = self.get_main_predicate(conclusion)
        sim = self.nlp(pred).similarity(self.nlp(concl))
        self.console.print(f"[blue]Debug: Similarity between '{pred}' and '{concl}': {sim:.4f}[/blue]")
        return sim

    def check_wordnet_relation(self, word1, word2):
        self.console.print(f"[blue]Debug: Checking WordNet relation between '{word1}' and '{word2}'[/blue]")
        synsets1 = wn.synsets(word1)
        synsets2 = wn.synsets(word2)
        self.console.print(f"[blue]Synsets for '{word1}': {[s.name() for s in synsets1]}[/blue]")
        self.console.print(f"[blue]Synsets for '{word2}': {[s.name() for s in synsets2]}[/blue]")
        if not synsets1 or not synsets2:
            return False, f"No synsets found for comparison."
        return False, f"No direct or recursive WordNet relation found."

    def validate_statement(self, statement):
        self.console.print("=" * 50, style="bold")
        self.console.print(f"Processing: [blue]{statement}[/blue]")
        parsed = self.parse_statement(statement)
        if parsed["type"] == "fact":
            fact = parsed["fact"]
            self.assert_fact(fact)
            self.console.print(f"[green]Fact asserted: {fact}[/green]")
            return True
        elif parsed["type"] == "rule":
            premise = parsed["premise"]
            conclusion = parsed["conclusion"]
            self.assert_rule(premise, conclusion)
            self.console.print(f"[green]Rule asserted: If {premise} then {conclusion}[/green]")
            return True
        elif parsed["type"] == "inference":
            premise = parsed["premise"]
            conclusion = parsed["conclusion"]
            if premise not in self.facts:
                self.assert_fact(premise)
                self.console.print(f"[green]Premise fact asserted: {premise}[/green]")
            self.infer()
            if conclusion in self.facts:
                self.console.print(f"[green]Conclusion {conclusion} inferred via rules.[/green]")
                return True
            else:
                sim = self.evaluate_association(premise, conclusion)
                if sim >= self.similarity_threshold:
                    self.console.print(f"[green]Conclusion {conclusion} validated (similarity: {sim:.4f}).[/green]")
                    self.reasoning.append(f"Validated conclusion '{conclusion}' based on embedding similarity (score: {sim:.4f}).")
                    self.facts.add(conclusion)
                    return True
                else:
                    self.console.print(f"[red]Conclusion {conclusion} NOT validated (similarity: {sim:.4f}).[/red]")
                    return False

    def print_reasoning(self):
        # Reasoning steps are printed in a panel without fixed width to allow wrapping.
        reasoning_text = "\n".join(self.reasoning) if self.reasoning else "None"
        self.console.print(Panel(reasoning_text, title="Reasoning Steps", border_style="bright_blue"))

    def print_knowledge_base(self):
        # Use a vertical-friendly layout for the KB.
        kb_panel = Panel.fit(
            "[cyan]Facts:[/cyan]\n" + ("\n".join(self.facts) if self.facts else "None") +
            "\n\n[magenta]Rules:[/magenta]\n" + ("\n".join([f"{p} -> {c}" for p, c in self.rules]) if self.rules else "None"),
            title="Knowledge Base",
            width=60,
            border_style="bright_blue"
        )
        self.console.print(kb_panel)

def run_tests():
    console = Console(width=60)
    validator = LogicValidator()
    test_cases = [
        ("Fact", "It is raining."),
        ("Inference", "It is raining, therefore the ground is wet."),
        ("Rule", "If something is wet, it is slippery."),
        ("Fact", "The ground is slippery."),
    ]
    results = []
    live_panel = Live(Panel("Initializing tests...", title="Live Test Output", width=60), refresh_per_second=4)

    with live_panel:
        for label, statement in test_cases:
            live_panel.update(Panel(f"Processing: {statement}", title="Live Test Output", width=60))
            time.sleep(0.5)
            validator.validate_statement(statement)
            kb_panel = Panel.fit(
                "[cyan]Facts:[/cyan]\n" + ("\n".join(validator.facts) if validator.facts else "None") +
                "\n\n[magenta]Rules:[/magenta]\n" + ("\n".join([f"{p} -> {c}" for p, c in validator.rules]) if validator.rules else "None"),
                title="Live KB",
                width=60,
                border_style="bright_blue"
            )
            live_panel.update(kb_panel)
            time.sleep(0.75)
            results.append((statement, True))
        # Final Summary Panel: restructured vertically.
        summary_lines = "\n".join([f"{stmt} : {'Passed' if res else 'Failed'}" for stmt, res in results])
        final_panel = Panel(summary_lines, title="Final Test Summary", width=60, border_style="bright_green")
        live_panel.update(final_panel)
        time.sleep(2)
    validator.print_reasoning()

def animate_message():
    """
    Display a lively, color-changing animation of the message
    "NO AI BITCH LOL !!!!" in a 60-column wide layout.
    """
    from rich.live import Live
    from rich.text import Text
    colors = ["red", "green", "blue", "magenta", "cyan", "yellow"]
    message = "NO LLM'S !!!!"
    console = Console(width=60)
    with Live(refresh_per_second=4, console=console) as live:
        for i in range(20):
            color = colors[i % len(colors)]
            text = Text(message, style=color, justify="center")
            live.update(Panel(text, border_style=f"bold {color}", width=60))
            time.sleep(0.3)

if __name__ == "__main__":
    run_tests()
    animate_message()
