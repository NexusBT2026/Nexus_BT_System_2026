"""
custom_ast.py: Custom AST-based code quality and compliance checks for productionization.

- Walks Python files in src/ and applies custom checks (e.g., missing docstrings, forbidden patterns, etc.).
- Designed for use with pre-commit or as a standalone script.

Usage:
    python src/utils/custom_ast.py [--dry-run]
    # Extend with more checks as needed.

Requirements:
    - Python 3.8+
"""
import ast
import os
import sys
import argparse


def check_missing_docstrings(filepath):
    """Return a list of function/class names missing docstrings."""
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source)
    missing = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not ast.get_docstring(node):
                missing.append((node.name, node.lineno))
    return missing


def main():
    parser = argparse.ArgumentParser(description="Custom AST-based code quality checks.")
    parser.add_argument('--dry-run', action='store_true', help='Show issues but do not fail.')
    args = parser.parse_args()
    src_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
    issues = []
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                missing = check_missing_docstrings(path)
                if missing:
                    for name, lineno in missing:
                        issues.append(f"{path}:{lineno} - {name} missing docstring")
    if issues:
        print("[AST CHECK] Missing docstrings:")
        for issue in issues:
            print("  -", issue)
        if not args.dry_run:
            sys.exit(1)
    else:
        print("[AST CHECK] All functions/classes have docstrings.")

if __name__ == "__main__":
    main()
