"""Workspace path validation utilities."""

from pathlib import Path
import os


def validate_workspace_path(path: Path) -> bool:
    """
    Ensure path is within workspace for security.

    Args:
        path: Path to validate

    Returns:
        True if path is within WORKSPACE_ROOT, False otherwise
    """
    try:
        workspace_root = Path(os.getenv("MCP_WORKSPACE_ROOT", Path.cwd()))
        resolved = path.resolve()
        workspace = workspace_root.resolve()
        resolved.relative_to(workspace)  # Raises ValueError if outside workspace
        return True
    except (ValueError, OSError):
        return False
