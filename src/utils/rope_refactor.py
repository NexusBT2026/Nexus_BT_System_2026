"""
rope_refactor.py: Automated refactoring tool using Rope for productionization.

- Performs batch refactoring operations (rename, extract method, etc.) on Python files in src/.
- Designed for use with pre-commit or as a standalone script.

Usage:
    python src/utils/rope_refactor.py --rename <old_name> <new_name> [--dry-run]
    # Extend with more refactoring options as needed.

Requirements:
    - Python 3.8+
    - rope (pip install rope)
"""
import os
import sys
import argparse
from rope.base.project import Project
from rope.refactor.rename import Rename


def find_symbol_offset(filepath, symbol):
    """Return the offset of the first occurrence of symbol in the file, or None if not found."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    idx = content.find(symbol)
    if idx == -1:
        return None
    return idx


def rename_symbol(project_root, resource_path, old_name, new_name, dry_run=False):
    offset = find_symbol_offset(resource_path, old_name)
    if offset is None:
        print(f"[ERROR] Symbol '{old_name}' not found in {resource_path}.")
        return
    project = Project(project_root)
    resource = project.get_file(resource_path)
    try:
        changes = Rename(project, resource, offset).get_changes(new_name)
        if dry_run:
            print(changes.get_description())
        else:
            project.do(changes)
            print(f"[INFO] Renamed {old_name} to {new_name} in {resource_path}")
    except Exception as e:
        print(f"[ERROR] Rope rename failed: {e}")
    finally:
        project.close()


def main():
    parser = argparse.ArgumentParser(description="Automate refactoring using Rope.")
    parser.add_argument('--rename', nargs=2, metavar=('OLD', 'NEW'), help='Rename symbol OLD to NEW')
    parser.add_argument('--file', type=str, help='Target Python file (relative to src/)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would change, but do not modify files.')
    args = parser.parse_args()
    src_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src')
    if args.rename and args.file:
        resource_path = os.path.join(src_dir, args.file)
        rename_symbol(src_dir, resource_path, args.rename[0], args.rename[1], dry_run=args.dry_run)
    else:
        print("[ERROR] --rename and --file are required.")
        sys.exit(1)

if __name__ == "__main__":
    main()
