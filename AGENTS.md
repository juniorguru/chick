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

Use the walrus operator (`:=`) to combine assignment and conditional checks for cleaner code. Always look for opportunities to use walrus operators in if statements and comprehensions.

**Example:**
```python
# Instead of:
result = some_function()
if result:
    use(result)

# Use:
if result := some_function():
    use(result)

# Instead of:
match = re.match(pattern, string)
if not match:
    raise ValueError()
owner, repo = match.groups()

# Use:
if not (match := re.match(pattern, string)):
    raise ValueError()
owner, repo = match.groups()
```

### Avoid Redundant Docstrings

If 99% of the value of a docstring can be inferred from the function name and its type signature, omit the docstring. Only add docstrings when they provide meaningful context beyond what the signature reveals.

**Bad:**
```python
def find_summary_comment(comments: list) -> str | None:
    """Find the last comment containing JSON summary data.
    
    Args:
        comments: List of comment objects from GitHub API
        
    Returns:
        Comment body string if found, None otherwise
    """
```

**Good:**
```python
def find_summary_comment(comments: list) -> str | None:
    # No docstring needed - name and signature are clear
```

## File Organization

### Prefer pathlib Over os.path

Always use `pathlib.Path` instead of `os.path` for file operations.

**Example:**
```python
# Use pathlib
from pathlib import Path
content = Path(__file__).parent / "fixtures" / "data.txt"

# Not os.path
import os
path = os.path.join(os.path.dirname(__file__), "fixtures", "data.txt")
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
1. Save real API responses as fixtures (markdown or text files)
2. Use Pydantic's TypeAdapter to reconstruct validated models
3. Test against realistic data with edge cases
4. Use mocking only when recording real responses is not feasible

### Test Structure and Style

**Prefer directness over abstraction in tests:**
- Use explicit values rather than loading from complex abstractions
- Example: `comment.body = Path("fixtures/data.md").read_text()` is better than `load_fixture("data")`

**Always use pytest.mark.parametrize for testing pure functions with various inputs:**
```python
@pytest.mark.parametrize(
    "url,expected",
    [
        ("https://github.com/owner/repo", ("owner", "repo")),
        ("https://github.com/owner/repo/", ("owner", "repo")),
    ],
)
def test_parse_url(url, expected):
    assert parse_url(url) == expected
```

**Test formatting:**
- Keep one empty line between setup code and asserts
- After an assert, if continuing with more code, add one empty line
- Strive for a minimum number of asserts per test
- When testing API responses, assert the whole response object rather than individual fields

**Never add docstrings to test functions** unless they add value beyond the function name. Test names should be descriptive enough.

**Example of good test structure:**
```python
@pytest.mark.asyncio
async def test_create_check_success(api):
    github_client = api.app["github_client"]
    issue_data = MagicMock(html_url="...", number=123)
    github_client.rest.issues.create.return_value = MagicMock(parsed_data=issue_data)

    resp = await api.post("/checks/testuser")
    data = await resp.json()

    assert resp.status == 200
    assert data == {"url": "...", "number": 123}
```

**Naming in tests:**
- Don't use `mock_` prefix everywhere - name variables by what they represent (`issue_data`, not `mock_issue_data`)
- Keep test code readable and clear
