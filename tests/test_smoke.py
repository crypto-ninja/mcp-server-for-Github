import importlib


def test_import_server():
    mod = importlib.import_module("github_mcp")
    assert hasattr(mod, "mcp")


def test_has_tools_registered():
    mod = importlib.import_module("github_mcp")
    # FastMCP stores tools on the instance; ensure at least one known tool exists by name in source
    assert hasattr(mod, "github_get_repo_info")

