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

## Code Style Guidelines

### Use Informative Logging Instead of Comments

Prefer log messages over code comments for describing what sections of code do. Comments should explain "why", not "what". Use logging with appropriate severity levels to make the code self-documenting.

**Bad:**
```python
# Get comments to check for summary
comments = get_comments()
```

**Good:**
```python
logger.info(f"Getting comments of issue #{issue_number} ({issue_data.state}) to check for summary")
comments = get_comments()
```

### Use Walrus Operator When Feasible

Use the walrus operator (`:=`) to combine assignment and conditional checks for cleaner code.

**Example:**
```python
# Instead of:
result = some_function()
if result:
    use(result)

# Use:
if result := some_function():
    use(result)
```

## Testing Guidelines

### Testing githubkit Code

When testing code that uses githubkit, prefer recording real API responses over mocking. This approach is more maintainable and catches real-world edge cases.

From the githubkit library creator (source: https://github.com/yanyongyu/githubkit/issues/98#issuecomment-2059235461):

> The easiest way is to record the response data and save it (dict, JSON file, etc.). You can export the api response data by `resp.text` (raw str data) or `resp.json()` (json parsed dict/list).
> 
> After save the response data, you could rebuild the validated data with powerful Pydantic methods:
> 
> ```python
> from pydantic import TypeAdapter
> from githubkit.versions.latest.models import SocialAccount
> 
> accounts: list[SocialAccount] = TypeAdapter(list[SocialAccount]).validate_json(json_content)
> accounts: list[SocialAccount] = TypeAdapter(list[SocialAccount]).validate_python(python_list)
> ```

**Best Practice:**
1. Save real API responses as fixtures (JSON files or Python dicts)
2. Use Pydantic's TypeAdapter to reconstruct validated models
3. Test against realistic data with edge cases
4. Use mocking only when recording real responses is not feasible

