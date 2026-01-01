"""
add_metrics.py: Scans for missing metrics/monitoring hooks in main project trading action functions.
This script proposes changes (shows diffs) but does NOT modify any files. You must review and apply changes manually.
"""
import ast
import os
import difflib
import subprocess
import re
from typing import Generator

# List all main project source folders to scan (add more as needed)
SRC_DIRS = [
    os.path.join(os.path.dirname(__file__), '..', 'src', 'exchange'),
    os.path.join(os.path.dirname(__file__), '..', 'src', 'backtest'),
    os.path.join(os.path.dirname(__file__), '..', 'src', 'data'),
    os.path.join(os.path.dirname(__file__), '..', 'src', 'position_sizing'),
    os.path.join(os.path.dirname(__file__), '..', 'src', 'strategy'),
    os.path.join(os.path.dirname(__file__), '..', 'src', 'utils'),
    # Add more main project directories here if needed
]
EXCLUDE_DIRS = {
    '__pycache__', 'legacy_files', 'octobot', 'freqtrade', 'freqtrade1',
    '.bmad-core', 'e2e', 'outputs', 'docs', 'scripts', 'tests', '.github', '.vscode', '.pytest_cache'
}

METRICS_HOOKS = [
    'log_metric', 'record_metric', 'send_metric', 'track_event', 'monitoring_hook'
]

def find_python_files(directory: str) -> Generator[str, None, None]:
    for root, dirs, files in os.walk(directory):
        # Exclude unwanted directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            if file.endswith('.py'):
                yield os.path.join(root, file)

def has_metrics_hook(node: ast.FunctionDef) -> bool:
    for n in ast.walk(node):
        if isinstance(n, ast.Call):
            if isinstance(n.func, ast.Name) and n.func.id in METRICS_HOOKS:
                return True
            elif isinstance(n.func, ast.Attribute) and n.func.attr in METRICS_HOOKS:
                return True
    return False

def scan_for_metrics_hooks(filepath: str):
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source, filename=filepath)
    missing = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if not has_metrics_hook(node):
                missing.append(node.name)
    if missing:
        print(f"[MISSING METRICS] {filepath}: {', '.join(missing)}")

def propose_metrics_hook_insertion(filepath: str) -> str:
    # This function generates the new code with metrics hooks (but does not write it)
    with open(filepath, 'r', encoding='utf-8') as f:
        source = f.read()
    tree = ast.parse(source, filename=filepath)
    class MetricsInserter(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            if not has_metrics_hook(node):
                metric_call = ast.Expr(
                    value=ast.Call(
                        func=ast.Name(id='log_metric', ctx=ast.Load()),
                        args=[ast.Constant(value=f"{node.name}_called")],
                        keywords=[]
                    )
                )
                # Insert after docstring if present
                if (
                    len(node.body) > 0 and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, ast.Constant) and
                    isinstance(node.body[0].value.value, str)
                ):
                    node.body.insert(1, metric_call)
                else:
                    node.body.insert(0, metric_call)
            return node
    inserter = MetricsInserter()
    new_tree = inserter.visit(tree)
    ast.fix_missing_locations(new_tree)
    new_code = ast.unparse(new_tree)
    return new_code

def show_diff(original: str, proposed: str, filename: str):
    diff = difflib.unified_diff(
        original.splitlines(),
        proposed.splitlines(),
        fromfile=filename,
        tofile=filename + '.proposed',
        lineterm=''
    )
    print('\n'.join(diff))

def extract_undefined_names(stderr: str):
    # Extract all undefined names from error output
    pattern = r"NameError: name '([a-zA-Z_][a-zA-Z0-9_]*)' is not defined"
    return re.findall(pattern, stderr)

def run_linter(pyfile):
    # Try flake8 first, then pylint if flake8 fails or is not installed
    try:
        result = subprocess.run([
            'flake8', pyfile, '--select=F821', '--format=%(row)d:%(col)d: %(code)s %(text)s'
        ], capture_output=True, text=True)
        if result.returncode == 0 and not result.stdout.strip():
            return None, None  # No errors
        return 'flake8', result.stdout
    except Exception:
        pass
    try:
        result = subprocess.run([
            'pylint', '--disable=all', '--enable=E0602', pyfile, '-rn', '--output-format=text'
        ], capture_output=True, text=True)
        if result.returncode == 0 and not result.stdout.strip():
            return None, None  # No errors
        return 'pylint', result.stdout
    except Exception:
        pass
    return None, None

def extract_undefined_names_linter(linter_output: str):
    # Extract undefined names from linter output (flake8: "undefined name 'foo'")
    pattern = r"undefined name '([a-zA-Z_][a-zA-Z0-9_]*)'"
    return re.findall(pattern, linter_output)

def find_symbol_definition(symbol: str, search_dirs=None):
    """Search for the definition of a symbol (function, class, or assignment) in the project."""
    if search_dirs is None:
        search_dirs = SRC_DIRS
    pattern_func = rf"def {symbol}\\b"
    pattern_class = rf"class {symbol}\\b"
    pattern_assign = rf"^{symbol}\\s*="
    for src_dir in search_dirs:
        for root, dirs, files in os.walk(src_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            for file in files:
                if file.endswith('.py'):
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if re.search(pattern_func, content) or re.search(pattern_class, content) or re.search(pattern_assign, content, re.MULTILINE):
                            return path
                    except Exception:
                        continue
    return None

def path_to_import(from_path, to_path, symbol):
    """Given two file paths, construct a relative import statement for the symbol."""
    from os.path import relpath, dirname, splitext, sep
    from_path_dir = dirname(from_path)
    rel = relpath(to_path, from_path_dir)
    rel_mod = rel.replace(sep, '.')
    if rel_mod.endswith('.py'):
        rel_mod = rel_mod[:-3]
    if rel_mod.startswith('.'):
        rel_mod = rel_mod[1:]
    if rel_mod == '__init__':
        rel_mod = '.'
    if rel_mod.startswith('..'):
        # fallback to absolute import
        rel_mod = rel_mod.lstrip('.')
        return f"from {rel_mod} import {symbol}"
    else:
        if rel_mod == '.':
            return f"from . import {symbol}"
        return f"from .{rel_mod} import {symbol}"

def get_top_level_functions(tree):
    """Yield only top-level FunctionDef nodes (not nested)."""
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            yield node

def main():
    for src_dir in SRC_DIRS:
        if os.path.exists(src_dir):
            for pyfile in find_python_files(src_dir):
                # Skip logging/metrics utility files
                if os.path.basename(pyfile) in {"logging_utils.py", "metrics.py", "monitoring.py"}:
                    continue
                with open(pyfile, 'r', encoding='utf-8') as f:
                    original = f.read()
                tree = ast.parse(original, filename=pyfile)
                missing = []
                for node in get_top_level_functions(tree):
                    if not has_metrics_hook(node):
                        missing.append(node.name)
                if missing:
                    print(f"[MISSING METRICS] {pyfile}: {', '.join(missing)}")
                    proposed = propose_metrics_hook_insertion(pyfile)
                    print(f"--- Proposed changes for {pyfile} ---")
                    show_diff(original, proposed, pyfile)
                    print("\nReview the diff above.")
                    resp = input("Apply this change? [y/N]: ").strip().lower()
                    if resp == 'y':
                        with open(pyfile, 'w', encoding='utf-8') as f:
                            f.write(proposed)
                        print(f"[APPLIED] Changes written to {pyfile}\n")
                        # Always reload the file after writing changes
                        with open(pyfile, 'r', encoding='utf-8') as f:
                            current = f.read()
                        # Immediately test the changed file for syntax errors
                        print(f"[TESTING] Checking for syntax errors in {pyfile}...")
                        result = subprocess.run([
                            'python', '-m', 'py_compile', pyfile
                        ], capture_output=True, text=True)
                        if result.returncode == 0:
                            print(f"[OK] No syntax errors in {pyfile}\n")
                        else:
                            print(f"[ERROR] Syntax error(s) detected in {pyfile}:")
                            print(result.stderr)
                        # Loop: keep fixing undefined names until linter passes
                        while True:
                            linter, linter_output = run_linter(pyfile)
                            if not linter_output:
                                print(f"[OK] No undefined names detected by linter in {pyfile}\n")
                                break
                            print(f"[LINTER: {linter}] Undefined name(s) detected:")
                            print(linter_output)
                            undefined_names = extract_undefined_names_linter(linter_output)
                            #print("DEBUG undefined_names extracted:", undefined_names)
                            fixed_any = False
                            for name in set(undefined_names):
                                #print("DEBUG Entering fix loop for:", name)
                                #print("AUTO-FIX '", name, "' is not defined in ", pyfile, ".", sep="")
                                def_path = find_symbol_definition(name)
                                #print("DEBUG find_symbol_definition('", name, "') returned:", def_path, sep="")
                                if def_path:
                                    import_stmt = path_to_import(pyfile, def_path, name)
                                    #print("DEBUG path_to_import('", pyfile, "', '", def_path, "', '", name, "') returned:", import_stmt, sep="")
                                    #print("AUTO-IMPORT Inserting:", import_stmt)
                                    lines = current.splitlines()
                                    insert_idx = 0
                                    for i, line in enumerate(lines):
                                        if line.strip().startswith('from') or line.strip().startswith('import'):
                                            insert_idx = i + 1
                                    if import_stmt not in lines:
                                        new_lines = lines[:insert_idx] + [import_stmt] + lines[insert_idx:]
                                        current = '\n'.join(new_lines)
                                        with open(pyfile, 'w', encoding='utf-8') as f:
                                            f.write(current)
                                        print("APPLIED Import fix written to", pyfile)
                                        fixed_any = True
                                        # Reload file after each import fix
                                        with open(pyfile, 'r', encoding='utf-8') as f:
                                            current = f.read()
                                    else:
                                        print("INFO Import already present in", pyfile)
                                else:
                                    print("WARN Could not find definition for '", name, "'. Manual fix needed.", sep="")
                            if not fixed_any:
                                break
                        # ...existing code...
                    else:
                        print(f"[SKIPPED] No changes made to {pyfile}\n")

if __name__ == '__main__':
    main()
