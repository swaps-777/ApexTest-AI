"""Shared LLM configuration for TestCases Generator AI Agent."""

from langchain_openai import ChatOpenAI

from config import LLM_MODEL, LLM_TEMPERATURE


llm = ChatOpenAI(
    model=LLM_MODEL,
    temperature=LLM_TEMPERATURE,
)