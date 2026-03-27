---
name: run-checks
description: Verify code changes are clean before considering a task done. Use this skill after making any code change — bug fix, feature, refactor. Always run the full check suite before declaring work complete.
---

# Run checks (coach project)

Run in this order — fix issues at each step before moving to the next:

```bash
ruff check . && ruff format .   # fix style issues first
mypy .                           # then type errors
pytest                           # then test failures
```

For a faster iteration loop, tail the output:
```bash
pytest -q 2>&1 | tail -10
mypy . 2>&1 | tail -10
```

**Target:** zero ruff errors, zero mypy errors, all tests passing.

If a test fails, diagnose the root cause — do not retry or skip. If mypy fails on a file you didn't touch, check whether your change broke an import or type signature elsewhere.
