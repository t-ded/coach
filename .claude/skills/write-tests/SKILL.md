---
name: write-tests
description: Testing conventions for the coach project. Use this skill whenever writing, editing, or reviewing tests — new test files, adding coverage, fixing a flaky test, anything. Always apply these conventions before writing test code.
---

# Testing conventions (coach project)

## Structure
- Tests live in a `tests/` subdirectory next to the module they test (e.g. `coach/builders/tests/`)
- Test class name mirrors the class under test: `TestRecentTrainingHistoryBuilder` tests `RecentTrainingHistoryBuilder`

## Setup
- Use `setup_method` for shared setup with sensible defaults; individual tests override only what's specific to them
- When all tests in a class share the same function call, make that call in `setup_method` and store the result; individual tests then assert on one aspect
- Use `setup_method`/`teardown_method` for class-scoped patches (start patcher in `setup_method`, stop in `teardown_method`)
- Never use `@pytest.fixture(autouse=True)` inside test classes

## Fakes over mocks
- Prefer **fakes** (minimal in-memory ABC implementations) over `MagicMock` for your own abstractions:
  ```python
  class FakeStravaTokenRepository(StravaTokenRepository):
      def __init__(self):
          self._tokens: dict[str, StravaTokens] = {}
      def get(self, user_id: str) -> Optional[StravaTokens]:
          return self._tokens.get(user_id)
  ```
- Reserve `MagicMock`/`patch` for genuinely external things you cannot control: Supabase `Client`, HTTP calls (`requests.post`), time

## Coverage
- Always cover unhappy paths and edge cases alongside the happy path: missing data, expired state, invalid input, `None` returns
- Test through public interfaces
- Test private helpers directly only when (a) the public interface is not unit-testable (e.g. Chainlit handlers) and (b) the helper has meaningful standalone logic

## Chainlit app tests
- Importing from a Chainlit app file requires stubbing `chainlit.server.server` before import
- Do this in a `conftest.py` in the same `tests/` directory (see `coach/web/tests/conftest.py` for the pattern)
