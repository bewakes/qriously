import ast
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parents[2]

PURE_FILES = [
    "accounts/policies.py",
    "credits/policies.py",
    "core/constants.py",
]
PURE_DIRS = ["lenses", "safety"]


def _iter_pure_files():
    for rel in PURE_FILES:
        path = SERVER_DIR / rel
        if path.exists():
            yield path
    for dirname in PURE_DIRS:
        directory = SERVER_DIR / dirname
        if directory.is_dir():
            yield from directory.rglob("*.py")


def _imports_django(path):
    tree = ast.parse(path.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names = [node.module or ""]
        else:
            continue
        if any(name == "django" or name.startswith("django.") for name in names):
            return True
    return False


def test_pure_modules_do_not_import_django():
    offenders = [str(path) for path in _iter_pure_files() if _imports_django(path)]
    assert offenders == [], f"pure modules import Django: {offenders}"
