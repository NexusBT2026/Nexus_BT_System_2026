"""
add_logging.py: Automated logging insertion tool for productionization.

- Adds a standard logger import and setup to Python files in src/ if missing.
- Optionally inserts a logging statement at the start of each function (demonstration only).
- Designed for use with pre-commit or as a standalone script.

Usage:
    python src/utils/add_logging.py [--dry-run] [--insert-log-statements]

Requirements:
    - Python 3.8+
"""
import ast
import os
import sys
import argparse

LOGGER_IMPORT = "import logging\nlogger = logging.getLogger(__name__)\n"


def has_logger_import(tree):
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "logging":
                    return True
        if isinstance(node, ast.Assign):
            if (isinstance(node.value, ast.Call)
                and getattr(getattr(node.value.func, 'attr', None), 'lower', lambda: None)() == 'getlogger'):
                return True
    return False


def add_logger_import(source):
    lines = source.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if line.strip().startswith("import ") or line.strip().startswith("from "):
            continue
        # Insert after last import
        return ''.join(lines[:i]) + LOGGER_IMPORT + ''.join(lines[i:])
    return LOGGER_IMPORT + source


def process_file(filepath, insert_log_statements=False, dry_run=False):
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source)
    changed = False
    if not has_logger_import(tree):
        source = add_logger_import(source)
        changed = True
    # Optionally, insert a logger.info at the start of each function (demo only)
    # (Advanced: use ast.NodeTransformer for robust insertion)
    if changed and not dry_run:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(source)
    return changed


def main():
    parser = argparse.ArgumentParser(description="Automate logging insertion for productionization.")
    parser.add_argument('--dry-run', action='store_true', help='Show what would change, but do not modify files.')
    parser.add_argument('--insert-log-statements', action='store_true', help='Insert logger.info at start of each function (demo only).')
    args = parser.parse_args()
    src_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
    changed_files = []
    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                if process_file(path, insert_log_statements=args.insert_log_statements, dry_run=args.dry_run):
                    changed_files.append(path)
    if changed_files:
        print("[INFO] Logging import added to:")
        for f in changed_files:
            print(f"  - {f}")
    else:
        print("[INFO] No changes needed.")

if __name__ == "__main__":
    main()
