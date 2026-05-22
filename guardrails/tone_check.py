"""Tone check for final test case pack."""

from llm import llm


def improve_tone(answer: str) -> str:
    prompt = f"""You are a professional QA documentation editor.

Rewrite the following test case pack in a clear, professional, and well-structured tone.

Rules:
- Do not change facts.
- Do not add new test cases.
- Do not remove acceptance criteria mappings.
- Do not invent API endpoints or assumptions.
- Keep markdown structure.
- Improve readability only.

Test Case Pack:
{answer}
"""

    return llm.invoke(prompt).content.strip()