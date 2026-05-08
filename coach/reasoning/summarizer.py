from coach.domain.session import Message
from coach.reasoning.providers import LLMProvider
from coach.reasoning.providers import create_llm_client

_SUMMARIZE_PROMPT = """\
Summarize the following coaching conversation as a structured training-state snapshot.

Output only the sections that have content — omit any heading whose section would be empty \
(do not write "None" or "N/A").

Use exactly these section headings when they apply:

**Active concerns**
Injuries, fatigue, pain, or health issues the user raised.

**Agreed training plan**
Specific workouts, weekly structure, or adjustments the coach committed to.

**Key decisions**
Target paces, race strategy, or training focus areas discussed and agreed.

**Open follow-ups**
Things the user said they would try or report back on.

Guidelines:
- Be factual and specific: include exact paces, distances, and workout names when mentioned.
- Omit sections that have no content — do not write "None" under any heading.
- Keep the total under 300 words.
- Focus on actionable training state, not conversational pleasantries.

Conversation:
{conversation}"""


class SessionSummarizer:
    def __init__(self, provider: LLMProvider, api_key: str) -> None:
        self._client = create_llm_client(provider=provider, api_key=api_key)

    def generate(self, messages: list[Message]) -> str:
        conversation = '\n'.join(f'{msg.role.capitalize()}: {msg.content}' for msg in messages)
        prompt = _SUMMARIZE_PROMPT.format(conversation=conversation)
        return self._client.complete(prompt)
