"""Section-level retrieval over the HR policy documents.

Each policy file is split on its '## ' headings, so every chunk is one policy section
and every answer can cite an exact document and section.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

POLICY_DIR = Path(__file__).resolve().parent.parent / "policies"

# A few HR words new hires use that policies phrase differently.
SYNONYMS = {
    "vacation": "pto paid time off",
    "holiday": "holidays pto",
    "salary": "pay paycheck",
    "paid": "pay paycheck payday",
    "insurance": "medical coverage",
    "health": "medical benefits",
    "401k": "401(k) retirement",
    "wfh": "remote work home",
    "computer": "laptop",
    "password": "login accounts mfa",
    "reimbursed": "reimbursement expenses",
    "sick": "sick leave",
    "roll": "carryover carry over",
    "leftover": "carryover unused",
    "wear": "dress code",
    "clothes": "dress code",
    "baby": "birth child qualifying life event",
    "married": "marriage qualifying life event",
    "abroad": "another country outside home country",
    "overseas": "another country outside home country",
    "india": "another country outside home country",
    "w4": "tax forms withholding",
}

# Words that appear in many sections and say little about which one is meant.
GENERIC_DF = 3


@dataclass
class Section:
    doc: str
    title: str
    text: str

    @property
    def citation(self) -> str:
        return f"{self.doc} > {self.title}"


def load_sections(policy_dir: Path = POLICY_DIR) -> list[Section]:
    sections: list[Section] = []
    for path in sorted(policy_dir.glob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        parts = re.split(r"^## +", path.read_text(encoding="utf-8"), flags=re.M)
        for part in parts[1:]:
            title, _, body = part.partition("\n")
            sections.append(Section(path.name, title.strip(), " ".join(body.split())))
    return sections


def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"\bw-4\b", "w4", text)
    return re.sub(r"401\(k\)", "401k", text)


def expand(query: str) -> str:
    query = normalize(query)
    words = re.findall(r"[a-z0-9]+", query)
    extra = [SYNONYMS[w] for w in words if w in SYNONYMS]
    return " ".join([query] + extra)


class Retriever:
    def __init__(self, sections: list[Section] | None = None):
        self.sections = sections or load_sections()
        docs = [normalize(f"{s.title} {s.title} {s.text}") for s in self.sections]
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), stop_words="english", sublinear_tf=True)
        self.matrix = self.vectorizer.fit_transform(docs)
        self.vocab = self.vectorizer.vocabulary_
        self.df = (self.matrix > 0).sum(axis=0).A1  # sections containing each term

    def specific_terms(self, query: str, section_index: int) -> list[str]:
        """Query terms found in the section that are rare across sections.

        If a question only matches common words like 'office' or 'work', no policy
        really covers it, and the assistant should say so instead of guessing.
        """
        analyzer = self.vectorizer.build_analyzer()
        terms = set(analyzer(expand(query)))
        row = self.matrix[section_index]
        return sorted(t for t in terms if t in self.vocab and row[0, self.vocab[t]] > 0
                      and self.df[self.vocab[t]] <= GENERIC_DF)

    def search(self, query: str, k: int = 3) -> list[tuple[Section, float]]:
        scores = cosine_similarity(self.vectorizer.transform([expand(query)]), self.matrix)[0]
        order = scores.argsort()[::-1][:k]
        return [(self.sections[i], float(scores[i])) for i in order]

    def index_of(self, section: Section) -> int:
        return self.sections.index(section)
