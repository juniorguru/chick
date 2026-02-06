# Agent Instructions

## Code Quality Checklist

Before completing any task, always run the following commands:

```bash
uv run ruff format .
uv run ruff check --fix .
uv run pytest
```

These commands ensure:
- Code is properly formatted
- Linting issues are fixed
- All tests pass

Do not mark a task as complete without running these checks.
