import ast
import json
import subprocess
import tempfile
from pathlib import Path

ALLOWED_IMPORTS = {"json", "pathlib", "collections", "math", "statistics"}


def _validate_ast(code: str) -> tuple[bool, str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return False, str(e)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            else:
                names = [node.module.split(".")[0]] if node.module else []
            for n in names:
                if n not in ALLOWED_IMPORTS:
                    return False, f"Import not allowed: {n}"
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in ("exec", "eval", "open", "__import__"):
                return False, f"Call not allowed: {node.func.id}"
    return True, "ok"


def run_fixture_script(code: str) -> dict:
    ok, msg = _validate_ast(code)
    if not ok:
        return {"ok": False, "error": msg, "stdout": ""}
    root = Path(__file__).resolve().parents[4]
    fixture = root / "fixtures" / "synthetic_only" / "incidents.json"
    if not fixture.exists():
        fixture.parent.mkdir(parents=True, exist_ok=True)
        fixture.write_text(json.dumps([{"modality": "text"}, {"modality": "image"}]))

    with tempfile.TemporaryDirectory() as td:
        script = Path(td) / "task.py"
        script.write_text(code)
        (Path(td) / "incidents.json").write_text(fixture.read_text())
        try:
            proc = subprocess.run(
            ["python3", str(script)],
            cwd=td,
            capture_output=True,
            text=True,
            timeout=5,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "TIMEOUT", "stdout": ""}
        return {
            "ok": proc.returncode == 0,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "error": None if proc.returncode == 0 else "EXEC_FAILED",
        }