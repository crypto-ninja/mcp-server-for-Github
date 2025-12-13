# Contributing to GitHub MCP Server

Thank you for your interest in contributing! This project follows the Model Context Protocol best practices and welcomes contributions.

## How to Contribute

### Reporting Issues

- Use GitHub Issues to report bugs or suggest features
- Provide clear descriptions and reproduction steps
- Include your Python version and OS

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the code style below
4. Add tests if applicable
5. Update documentation as needed
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## Code Style

### Python Style Guide

- Follow PEP 8
- Use type hints for all functions
- Use async/await for I/O operations
- Add comprehensive docstrings
- Use Pydantic models for input validation

### MCP Best Practices

- Tools should be action-oriented and descriptive
- Use the `github_` prefix for all tool names
- Support both JSON and Markdown response formats
- Implement proper error handling
- Respect the 25,000 character limit

### Documentation

- Update README.md for new features
- Add examples to FEATURES.md
- Update ARCHITECTURE.md if design changes
- Keep docstrings comprehensive

## Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/github-mcp-server.git
cd github-mcp-server

# Install dependencies
pip install -r requirements.txt

# Install package in editable mode
pip install -e .

# Verify imports work
python -c "from github_mcp.server import run; print('✅ Package imports work')"

# Run tests
# (Add test commands when available)
```

## Adding New Tools

When adding a new tool:

1. Create a Pydantic input model with validation
2. Implement the async tool function with proper docstrings
3. Use shared utilities for API requests and error handling
4. Add tool to the README documentation
5. Create examples in FEATURES.md
6. Add test scenarios to evaluation.xml

Example structure:

```python
class NewToolInput(BaseModel):
    """Input model for new tool."""
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'
    )
    
    param: str = Field(..., description="Parameter description")

@mcp.tool(
    name="github_new_tool",
    annotations={
        "title": "Tool Title",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def github_new_tool(params: NewToolInput) -> str:
    """
    Comprehensive docstring explaining:
    - What the tool does
    - When to use it
    - Parameters
    - Return format
    - Error handling
    """
    try:
        # Implementation
        pass
    except Exception as e:
        return _handle_api_error(e)
```

## Testing

- Test with real GitHub API calls
- Verify error handling for edge cases
- Check both JSON and Markdown formats
- Test pagination for large result sets
- Verify character limit truncation

## Questions?

Feel free to open an issue for questions or join discussions!

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Help others learn and grow
- Follow the golden rule

Thank you for contributing! 🎉
