import ast
import json
from flask import Flask, render_template_string, request, jsonify

from linter import SemanticAnalyzer

app = Flask(__name__)


def analyze_code(source_code, filename="snippet.py"):
    try:
        tree = ast.parse(source_code, filename=filename)
    except SyntaxError as exc:
        return [{
            "file": filename,
            "line": exc.lineno or 1,
            "col": exc.offset or 0,
            "level": "ERROR",
            "message": f"Syntax error: {exc.msg}"
        }]

    analyzer = SemanticAnalyzer(filename=filename)
    analyzer.visit(tree)
    analyzer.check_unused_symbols()
    return analyzer.errors


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Compiler Design PBL - Static Code Analyzer</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col items-center p-6">
    <div class="w-full max-w-5xl">
        <header class="mb-8 text-center">
            <h1 class="text-3xl font-bold tracking-tight text-indigo-400">Python Static Code Analyzer &amp; Linter</h1>
            <p class="text-slate-400 mt-2">Compiler Design PBL Project — AST Analysis, Symbol Tables, and Semantic Rule Checking</p>
        </header>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div class="flex flex-col bg-slate-800 p-4 rounded-xl border border-slate-700 shadow-lg">
                <label for="code-input" class="text-sm font-semibold text-slate-300 mb-2">Paste Python Source Code:</label>
                <textarea id="code-input" rows="14" class="w-full bg-slate-950 font-mono text-sm p-3 rounded-lg border border-slate-700 focus:outline-none focus:border-indigo-500 text-emerald-300 resize-none" placeholder="def my_function():
    x = 10
    eval('print(x)')">def outer_math(factor):
    multiplier = factor

    def inner_op(n):
        return n * multiplier

    return inner_op(5)</textarea>
                <button onclick="runLinter()" class="mt-4 bg-indigo-600 hover:bg-indigo-500 text-white font-medium py-2.5 px-4 rounded-lg transition duration-200 shadow-md">
                    Analyze Code 🚀
                </button>
            </div>

            <div class="flex flex-col bg-slate-800 p-4 rounded-xl border border-slate-700 shadow-lg">
                <span class="text-sm font-semibold text-slate-300 mb-2">Analysis Report &amp; Diagnostics:</span>
                <div id="output-panel" class="w-full h-72 md:h-[356px] bg-slate-950 font-mono text-xs p-3 rounded-lg border border-slate-700 overflow-y-auto text-slate-400">
                    <span class="text-slate-500">Ready. Paste code and click 'Analyze Code' to run AST validation and scope checks.</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        async function runLinter() {
            const code = document.getElementById('code-input').value;
            const outputPanel = document.getElementById('output-panel');

            outputPanel.innerHTML = '<span class="text-indigo-400">Running Lexical, Syntax, and Semantic Analysis...</span>';

            try {
                const response = await fetch('/api/lint', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code })
                });

                if (!response.ok) {
                    throw new Error('Request failed');
                }

                const data = await response.json();
                const errors = data.errors || [];

                if (!errors.length) {
                    outputPanel.innerHTML = '<span class="text-emerald-400">No issues found. Code is clean.</span>';
                    return;
                }

                outputPanel.innerHTML = errors.map(err => {
                    const levelClass = err.level === 'ERROR' ? 'text-red-400' : 'text-yellow-400';
                    return `<div class="mb-2 ${levelClass}">[${err.level}] ${err.file}:${err.line}:${err.col} - ${err.message}</div>`;
                }).join('');
            } catch (error) {
                outputPanel.innerHTML = '<span class="text-red-400">An error occurred while analyzing the code.</span>';
            }
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/lint', methods=['POST'])
def lint_api():
    payload = request.get_json(silent=True) or {}
    code = payload.get('code', '')
    if not isinstance(code, str):
        return jsonify({"status": "error", "errors": [{"file": "snippet.py", "line": 1, "col": 0, "level": "ERROR", "message": "Request body must include a code string."}]})

    return jsonify({"status": "ok", "errors": analyze_code(code)})


if __name__ == '__main__':
    app.run(debug=True)
