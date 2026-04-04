---
name: github-workflow
description: Git and GitHub workflow rules for the coach project. Use this skill before committing, creating PRs, merging, or closing issues. These rules are non-negotiable for keeping history clean and master stable.
---

# GitHub workflow (coach project)

## Branch protection
- `master` is protected — never push directly. All changes go through a PR.

## Commits
- One coherent, independently buildable change per commit (one refactor, one feature, one fix)
- Never mix unrelated changes in a single commit

## Pull requests
- Always rebase merge: `gh pr merge --rebase` (not squash or merge commits)
- **Always `git push` before `gh pr merge --rebase`** — the command merges the remote branch; local-only commits not yet pushed are silently left behind
- Always check that the CI has passed after pushing to the remote branch - do not report success before you can report also success on CI

## Issues
- `gh issue close` accepts one issue at a time — loop for multiple:
  ```bash
  for i in 1 2 3; do gh issue close $i; done
  ```
- `gh issue view` emits a GraphQL deprecation warning to stderr; suppress with `--json title,body`

## Notes
- `.claude/CLAUDE.md` is tracked by git (`.claude/*` is ignored except `CLAUDE.md`)
- `gh pr merge` with an open worktree may require care
