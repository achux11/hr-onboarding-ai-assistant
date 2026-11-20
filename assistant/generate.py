"""Answer generation for the RAG assistant.

The retriever picks the policy section; a generator writes the answer from that section only.

  ExtractiveGenerator  no model: returns the most relevant sentences (default, repeatable)
  ClaudeGenerator      Claude via the Anthropic API (needs ANTHROPIC_API_KEY)
  HFGenerator          an open model run locally with Hugging Face transformers (e.g. in Colab)
"""
from __future__ import annotations

import os
import re

SYSTEM = (
    "You are an HR onboarding assistant for Example Co. Answer the new hire's question using ONLY "
    "the policy text provided. Keep the answer to 1-3 sentences and keep exact numbers, days and "
    "amounts from the policy. If the policy text does not answer the question, reply exactly: "
    "I don't know, please ask HR."
)
IDK = "i don't know"


def user_prompt(question: str, policy_title: str, policy_text: str) -> str:
    return f"Policy section: {policy_title}\n{policy_text}\n\nQuestion: {question}"


class ExtractiveGenerator:
    name = "extractive"

    def __call__(self, question: str, title: str, text: str) -> str:
        q = set(re.findall(r"[a-z0-9]+", question.lower()))
        sentences = re.split(r"(?<!\bCo)(?<=[.!?])\s+", text)
        ranked = sorted(sentences, key=lambda s: -len(q & set(re.findall(r"[a-z0-9]+", s.lower()))))
        keep = set(ranked[:2])
        return " ".join(s for s in sentences if s in keep)


class ClaudeGenerator:
    def __init__(self, model: str | None = None):
        import anthropic  # optional dependency

        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError("Set ANTHROPIC_API_KEY to use Claude.")
        self.client = anthropic.Anthropic()
        self.model = model or os.getenv("HR_ASSISTANT_MODEL", "claude-haiku-5-5")
        self.name = f"claude:{self.model}"

    def __call__(self, question: str, title: str, text: str) -> str:
        msg = self.client.messages.create(
            model=self.model, max_tokens=200, temperature=0, system=SYSTEM,
            messages=[{"role": "user", "content": user_prompt(question, title, text)}],
        )
        return msg.content[0].text.strip()


class HFGenerator:
    def __init__(self, model: str = "Qwen/Qwen2.5-1.5B-Instruct"):
        from transformers import pipeline  # optional dependency

        self.pipe = pipeline("text-generation", model=model, device_map="auto")
        self.name = f"hf:{model}"

    def __call__(self, question: str, title: str, text: str) -> str:
        messages = [{"role": "system", "content": SYSTEM},
                    {"role": "user", "content": user_prompt(question, title, text)}]
        out = self.pipe(messages, max_new_tokens=150, do_sample=False)
        return out[0]["generated_text"][-1]["content"].strip()


def make(backend: str, model: str | None = None):
    if backend == "extractive":
        return ExtractiveGenerator()
    if backend == "claude":
        return ClaudeGenerator(model)
    if backend == "hf":
        return HFGenerator(model) if model else HFGenerator()
    raise ValueError(f"unknown backend: {backend}")
