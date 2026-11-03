import ast
import sys
import os
import json
import argparse
from colorama import init, Fore, Style

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)


class Scope:
    """Represents a lexical scope (Global, Function, or Class) for the Symbol Table."""
    def __init__(self, name: str, scope_type: str = 'local', parent=None):
        self.name = name
        self.scope_type = scope_type  # 'global', 'function', 'class'
        self.parent = parent
        self.children = []
        self.symbols = {}  # name -> { 'node': node, 'assigned': bool, 'used': bool }
        
        if parent:
            parent.children.append(self)

    def define(self, name: str, node, assigned: bool = True):
        """Define a symbol in the current scope."""
        self.symbols[name] = {'node': node, 'assigned': assigned, 'used': False}

    def resolve(self, name: str):
        """Look up a symbol in the current scope, traversing up to parent scopes (Closures/Globals)."""
        curr = self
        while curr:
            if name in curr.symbols:
                return curr, curr.symbols[name]
            curr = curr.parent
        return None, None


class SemanticAnalyzer(ast.NodeVisitor):
    """Combined AST Visitor for building symbol tables, tracking scopes, and linting rules."""
    def __init__(self, filename: str):
        self.filename = filename
        self.global_scope = Scope(name="global", scope_type="global")
        self.current_scope = self.global_scope
        self.errors = []

    def report(self, node, message: str, level: str = "WARNING"):
        self.errors.append({
            'file': self.filename,
            'line': getattr(node, 'lineno', 1),
            'col': getattr(node, 'col_offset', 0),
            'level': level,
            'message': message
        })

    # --- Scope & Symbol Table Management ---

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Define function name in enclosing scope
        self.current_scope.define(node.name, node, assigned=True)
        
        # Enter new function scope
        func_scope = Scope(name=node.name, scope_type="function", parent=self.current_scope)
        prev_scope = self.current_scope
        self.current_scope = func_scope

        # Define function arguments in local scope
        for arg in node.args.args:
            self.current_scope.define(arg.arg, node, assigned=True)

        # Visit function body
        for stmt in node.body:
            self.visit(stmt)

        # Restore previous scope
        self.current_scope = prev_scope

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.current_scope.define(target.id, target, assigned=True)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        if isinstance(node.ctx, ast.Load):
            _, symbol_info = self.current_scope.resolve(node.id)
            if symbol_info:
                symbol_info['used'] = True
        self.generic_visit(node)

    # --- Semantic Linting Rules ---

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id == 'eval':
                self.report(
                    node, 
                    "Use of 'eval()' detected. Severe security risk (Arbitrary Code Execution vulnerability).", 
                    level="ERROR"
                )
            elif node.func.id == 'exec':
                self.report(
                    node, 
                    "Use of 'exec()' detected. Avoid executing dynamic untrusted code strings.", 
                    level="WARNING"
                )
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        if len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
            self.report(
                node, 
                "Empty 'except:' block with 'pass' detected. Exceptions should be handled or logged.", 
                level="WARNING"
            )
        self.generic_visit(node)

    def check_unused_symbols(self, scope: Scope = None):
        """Recursively checks symbol table tree for local variables that were never referenced."""
        if scope is None:
            scope = self.global_scope

        for name, info in scope.symbols.items():
            # Only flag unused variables inside functions, ignoring function definitions (closures/helpers)
            if scope.scope_type == 'function':
                if not isinstance(info['node'], ast.FunctionDef):
                    if not info['used'] and not name.startswith('_'):
                        node = info['node']
                        self.errors.append({
                            'file': self.filename,
                            'line': getattr(node, 'lineno', 1),
                            'col': getattr(node, 'col_offset', 0),
                            'level': 'WARNING',
                            'message': f"Unused local variable '{name}' in function '{scope.name}'."
                        })
                        
        for child in scope.children:
            self.check_unused_symbols(child)


class LinterEngine:
    """Orchestrates the entire compilation/analysis pipeline for target files."""
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.errors = []

    def analyze(self) -> list:
        if not os.path.exists(self.filepath):
            print(f"{Fore.RED}[FATAL ERROR] File '{self.filepath}' does not exist.{Style.RESET_ALL}")
            sys.exit(1)

        with open(self.filepath, 'r', encoding='utf-8') as f:
            source_code = f.read()

        # Phase 1: Lexical & Syntax Parsing
        try:
            tree = ast.parse(source_code, filename=self.filepath)
        except SyntaxError as e:
            print(f"{Fore.RED}[SYNTAX ERROR] {self.filepath}:{e.lineno}:{e.offset} - {e.msg}{Style.RESET_ALL}")
            sys.exit(1)

        # Phase 2 & 3: Symbol Table Building & Semantic Analysis
        analyzer = SemanticAnalyzer(filename=self.filepath)
        analyzer.visit(tree)
        analyzer.check_unused_symbols()

        return analyzer.errors


def main():
    parser = argparse.ArgumentParser(
        description="Object-Oriented Static Code Analyzer & Linter for Python (Compiler Design PBL)",
        epilog="Example: python linter.py target_file.py --output report.json"
    )
    parser.add_argument("file", help="Path to the Python source file to lint")
    parser.add_argument(
        "-o", "--output",
        help="Path to export linter results as a JSON report file",
        default=None
    )
    args = parser.parse_args()

    engine = LinterEngine(args.file)
    errors = engine.analyze()

    # Export to JSON if requested
    if args.output:
        try:
            with open(args.output, 'w', encoding='utf-8') as json_file:
                json.dump(errors, json_file, indent=4)
            print(f"{Fore.GREEN}✔ Linter results successfully exported to JSON: {args.output}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}[ERROR] Failed to write JSON output to '{args.output}': {e}{Style.RESET_ALL}")

    # Console Output Formatting (GCC / ESLint Style)
    print(f"\n{Style.BRIGHT}Running Static Analyzer on '{args.file}'...{Style.RESET_ALL}")
    
    if not errors:
        print(f"{Fore.GREEN}✔ Zero issues found! Codebase is clean.{Style.RESET_ALL}\n")
        sys.exit(0)
    else:
        error_count = sum(1 for e in errors if e['level'] == 'ERROR')
        warning_count = sum(1 for e in errors if e['level'] == 'WARNING')
        
        print(f"Found {len(errors)} issue(s) ({error_count} errors, {warning_count} warnings):\n")
        
        for err in sorted(errors, key=lambda x: (x['line'], x['col'])):
            level_color = Fore.RED if err['level'] == 'ERROR' else Fore.YELLOW
            prefix = f"{level_color}[{err['level']}]{Style.RESET_ALL}"
            location = f"{Fore.CYAN}{err['file']}:{err['line']}:{err['col']}{Style.RESET_ALL}"
            print(f"{location} - {prefix} {err['message']}")
        
        print()
        sys.exit(1 if error_count > 0 else 0)


if __name__ == "__main__":
    main()