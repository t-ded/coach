from coach.domain.session import Message
from coach.reasoning.providers import LLMProvider
from coach.reasoning.providers import create_llm_client

_SUMMARIZE_PROMPT = """\
Summarize the following coaching conversation concisely. Focus on:
- Key topics discussed (e.g. training plans, race goals, injury concerns)
- Decisions made or advice given
- Any commitments or follow-up items

Keep the summary factual and under 300 words.

Conversation:
{conversation}

Summary:"""


class SessionSummarizer:
    def __init__(self, provider: LLMProvider, api_key: str) -> None:
        self._client = create_llm_client(provider=provider, api_key=api_key)

    def generate(self, messages: list[Message]) -> str:
        conversation = '\n'.join(f'{msg.role.capitalize()}: {msg.content}' for msg in messages)
        prompt = _SUMMARIZE_PROMPT.format(conversation=conversation)
        return self._client.complete(prompt)
