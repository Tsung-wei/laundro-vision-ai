# AGENTS.md

This file provides guidance to agents when working with code in this repository.

- Package manager is `uv`; prefix all Python commands with `uv run` (e.g., `uv run pytest`, `uv run ruff`)
- You SHALL use Python 3.11+ modern syntax; Use absolute import over relative import; DO not use inline import inside
  classes/methods.
- Coverage must meet 90% minimum (`fail_under = 90` in `pyproject.toml`)
- Pre-commit runs in order: ruff (lint) -> ruff-format -> pyright (typecheck) -> commitizen (conventional commits)
- Commitizen enforces conventional commit format (e.g., `feat: add foo`, `fix: bar`)
- Ruff enforces double quotes for strings (`quote-style = "double"` in config)
- Pre-commit blocks direct commits to `main`; use conventional commit messages
- Pyright type checking runs on `src/laundro_vision_ai/` and `tests/` via pre-commit
- Unused local variables are unfixable by Ruff (`unfixable = ["F841"]`); prefix with `_` or remove
- Python test files must follow `test_*.py` naming (enforced by pre-commit hook)
- Use `git commit` instead of `uv run cz commit`
