# ~/formalities/playground/correlatewetwithrain.py
#!/usr/bin/env python
"""
CorrelateWetWithRain.py

This script continuously explores relationships between the words “rain” and “wet”
using multiple approaches (derived from WordNet, spaCy embeddings, recursive token analysis,
and combined scoring). It cycles through different configurations until one of the methods
produces a strong association, and it displays detailed, visually appealing debug output
so that you can see exactly which configuration made it “work.”

No hardcoded inference rules are used—the system dynamically searches and refines its parameters.
"""

import time
import itertools
import nltk
from nltk.corpus import wordnet as wn
import spacy
from rich.console import Console
from rich.table import Table
import string
from collections import deque

# Download required NLTK resources if needed.
#nltk.download('wordnet')
#nltk.download('omw-1.4')

console = Console()
nlp = spacy.load("en_core_web_md")

# A simple set of stopwords for filtering definitions.
STOPWORDS = {"the", "a", "an", "of", "or", "with", "and", "to", "in", "on", "by", "for", "at"}

def tokenize_definition(definition):
    """Remove punctuation, lowercase, and filter out stopwords."""
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

# ---------------------------
# Approach 1: Derivational Mapping
# ---------------------------
def approach_derivational_mapping(word_adj, target_noun):
    console.print("[bold]Approach 1: Derivational Mapping[/bold]")
    results = []
    for syn in wn.synsets(word_adj, pos=wn.ADJ):
        for lemma in syn.lemmas():
            deriv_related = lemma.derivationally_related_forms()
            for d in deriv_related:
                if target_noun in d.name().lower():
                    results.append((syn.name(), d.synset().name()))
    if results:
        console.print(f"[green]Mapping found from '{word_adj}' to '{target_noun}':[/green] {results}")
    else:
        console.print(f"[red]No mapping found from '{word_adj}' to '{target_noun}'.[/red]")
    return results

# ---------------------------
# Approach 2: Word Embeddings (Cosine Similarity)
# ---------------------------
def approach_word_embeddings(word1, word2):
    console.print("[bold]Approach 2: Word Embeddings (Cosine Similarity)[/bold]")
    doc1 = nlp(word1)
    doc2 = nlp(word2)
    sim = doc1.similarity(doc2)
    console.print(f"Cosine similarity between [blue]{word1}[/blue] and [blue]{word2}[/blue]: [magenta]{sim:.4f}[/magenta]")
    return sim

# ---------------------------
# Approach 3: Graph Search Over WordNet
# ---------------------------
def approach_graph_search(word1, word2, max_depth=3):
    console.print("[bold]Approach 3: Graph Search Over WordNet[/bold]")
    paths_found = []
    synsets1 = wn.synsets(word1)
    synsets2 = wn.synsets(word2)
    for s1 in synsets1:
        visited = set()
        queue = deque([(s1, [s1])])
        while queue:
            current, path = queue.popleft()
            if current in synsets2:
                paths_found.append(path)
                break
            if len(path) >= max_depth:
                continue
            neighbors = current.hypernyms() + current.hyponyms()
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
    if paths_found:
        for path in paths_found:
            console.print(" -> ".join([p.name() for p in path]), style="green")
    else:
        console.print("[red]No connecting path found within max depth.[/red]")
    return paths_found

# ---------------------------
# Approach 4: Dynamic Threshold Testing (Wu-Palmer)
# ---------------------------
def approach_dynamic_threshold(word1, word2, thresholds=[0.1, 0.2, 0.3, 0.4, 0.5]):
    console.print("[bold]Approach 4: Dynamic Threshold Testing (Wu-Palmer)[/bold]")
    synsets1 = wn.synsets(word1)
    synsets2 = wn.synsets(word2)
    results = {}
    for thresh in thresholds:
        found = False
        best = 0.0
        best_pair = None
        for s1 in synsets1:
            for s2 in synsets2:
                sim = s1.wup_similarity(s2)
                if sim is not None and sim >= thresh and sim > best:
                    best = sim
                    best_pair = (s1.name(), s2.name())
                    found = True
        results[thresh] = (found, best, best_pair)
        console.print(f"Threshold [cyan]{thresh:.2f}[/cyan]: Found = [magenta]{found}[/magenta], Best similarity = [magenta]{best:.2f}[/magenta] for pair: [magenta]{best_pair}[/magenta]")
    return results

# ---------------------------
# Approach 5: Combined Signal
# ---------------------------
def approach_combined(word1, word2, wup_weight=0.5, embed_weight=0.5):
    console.print(f"[bold]Approach 5: Combined Signal (wup_weight={wup_weight}, embed_weight={embed_weight})[/bold]")
    synsets1 = wn.synsets(word1)
    synsets2 = wn.synsets(word2)
    best_wup = 0.0
    best_pair = None
    for s1 in synsets1:
        for s2 in synsets2:
            sim = s1.wup_similarity(s2)
            if sim is not None and sim > best_wup:
                best_wup = sim
                best_pair = (s1.name(), s2.name())
    embed_sim = approach_word_embeddings(word1, word2)
    combined_score = wup_weight * best_wup + embed_weight * embed_sim
    console.print(f"Best Wu-Palmer similarity: [magenta]{best_wup:.4f}[/magenta] (pair: [magenta]{best_pair}[/magenta])")
    console.print(f"Word Embedding similarity: [magenta]{embed_sim:.4f}[/magenta]")
    console.print(f"Combined score: [magenta]{combined_score:.4f}[/magenta]")
    return combined_score

# ---------------------------
# Approach 6: Hybrid Recursive Common Token Intersection
# ---------------------------
def approach_recursive_common_tokens(word1, word2, max_depth=3):
    console.print(f"[bold]Approach 6: Hybrid Recursive Common Token Intersection (depth={max_depth})[/bold]")
    synsets1 = wn.synsets(word1)
    synsets2 = wn.synsets(word2)
    best_overlap = 0.0
    best_pair = None
    for s1 in synsets1:
        tokens1 = collect_recursive_definitions(s1, max_depth=max_depth)
        console.print(f"[blue]Synset {s1.name()} tokens:[/blue] {tokens1}")
        for s2 in synsets2:
            tokens2 = collect_recursive_definitions(s2, max_depth=max_depth)
            console.print(f"[blue]Synset {s2.name()} tokens:[/blue] {tokens2}")
            if not tokens1 or not tokens2:
                continue
            intersection = tokens1.intersection(tokens2)
            union = tokens1.union(tokens2)
            overlap = len(intersection) / len(union) if union else 0.0
            console.print(f"[blue]Overlap between {s1.name()} and {s2.name()}: {overlap:.2f} (common: {intersection})[/blue]")
            if overlap > best_overlap:
                best_overlap = overlap
                best_pair = (s1.name(), s2.name())
    console.print(f"Best recursive token overlap: [magenta]{best_overlap:.2f}[/magenta] for pair: [magenta]{best_pair}[/magenta]")
    return best_overlap, best_pair

# ---------------------------
# Continuous Exploration Loop
# ---------------------------
def explore_relationship(word1, word2, success_combined=0.60, success_overlap=0.20):
    """
    Continuously try various approaches and parameter configurations until
    a "successful" association is found. Success is defined as either a combined
    score (Approach 5) above success_combined OR a recursive token overlap (Approach 6)
    above success_overlap.
    """
    iteration = 0
    best_overall = {"approach": None, "score": 0, "details": None}
    while True:
        iteration += 1
        console.rule(f"Iteration {iteration}")
        results_table = Table(title="Current Exploration Results")
        results_table.add_column("Approach", style="cyan")
        results_table.add_column("Parameters / Config", style="yellow")
        results_table.add_column("Score", style="magenta")

        # Approach 2: Word Embeddings (static)
        emb_sim = approach_word_embeddings(word1, word2)
        results_table.add_row("Word Embeddings", "N/A", f"{emb_sim:.4f}")

        # Approach 5: Combined Signal: try different weight combinations
        best_combined = 0.0
        best_params = None
        for wup_weight, embed_weight in itertools.product([i/10 for i in range(0, 11)], repeat=2):
            if abs(wup_weight + embed_weight - 1.0) > 1e-6:
                continue  # enforce weights sum to 1
            score = approach_combined(word1, word2, wup_weight, embed_weight)
            results_table.add_row("Combined Signal", f"wup={wup_weight:.1f}, embed={embed_weight:.1f}", f"{score:.4f}")
            if score > best_combined:
                best_combined = score
                best_params = (wup_weight, embed_weight)

        # Approach 6: Recursive Token Intersection: try different recursion depths
        best_overlap = 0.0
        best_config = None
        for depth in range(2, 7):
            overlap, pair = approach_recursive_common_tokens(word1, word2, max_depth=depth)
            results_table.add_row("Recursive Tokens", f"depth={depth}", f"{overlap:.2f}")
            if overlap > best_overlap:
                best_overlap = overlap
                best_config = depth

        console.print(results_table)

        # Update best overall if applicable:
        if best_combined > best_overall["score"]:
            best_overall = {"approach": "Combined Signal", "score": best_combined, "details": best_params}
        if best_overlap > best_overall["score"]:
            best_overall = {"approach": "Recursive Tokens", "score": best_overlap, "details": best_config}

        console.print(f"[bold]Best Overall So Far:[/bold] {best_overall}")

        # Check for success:
        if best_combined >= success_combined or best_overlap >= success_overlap:
            console.print("[green bold]SUCCESS: A strong association has been detected![/green bold]")
            console.print(f"Final Best Overall: {best_overall}")
            break
        else:
            console.print("[red]No strong association yet; re-exploring with new configurations...[/red]")
            time.sleep(1)  # slight delay before next iteration

def main():
    console.print("[bold underline]Exploring Relationship Between 'rain' and 'wet'[/bold underline]\n")
    explore_relationship("rain", "wet")

if __name__ == "__main__":
    main()
