---
name: python-conventions
description: Code style and structure conventions for this Python project. Use this skill whenever writing, editing, or reviewing any Python code in the coach repo — new modules, bug fixes, refactors, anything. Do not write code without consulting these conventions first.
---

# Python conventions (coach project)

## Toolchain
- Python 3.13+, strict mypy, ruff (line length 200)
- Single-quote strings enforced by ruff (`Q001`)
- Imports: force-single-line (one import per line, no grouped imports)

## Type annotations
- All functions must be fully typed — no untyped parameters or return values
- Use `Optional[X]` not `X | None`
- Use `ABC` + `@abstractmethod` for interfaces — not `Protocol` (explicit inheritance and runtime enforcement preferred over structural subtyping)

## Code style
- Prefer intermediate variable assignments over deeply nested calls:
  ```python
  # good
  raw = client.fetch()
  result = process(raw)

  # bad
  result = process(client.fetch())
  ```
- Comments only when intent cannot be made clear through naming — never restate what the code does
- Private helpers within a module rather than a separate helper module, unless the logic is genuinely reused elsewhere or completely independent
- Wrapper functions that only add a fixed set of arguments to another call are not worth naming — inline them
- Single-responsibility functions: a function either owns the full setup (constructs deps + does the work) or accepts pre-loaded data and acts on it — never both
- `datetime.UTC` not `timezone.UTC`
- Remove dead code (unused imports, dataclasses, methods) promptly

## After any change
Review the affected code for simplification opportunities, duplication, and violations of the above before considering the task done.
