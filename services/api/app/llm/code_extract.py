"""Extract runnable Python from model output (plain or markdown fenced)."""

import ast
import re


def extract_python_code(raw: str) -> tuple[str | None, str | None]:
    """
    Return (code, error). error is set when input cannot be normalized safely.
    """
    text = (raw or "").strip()
    if not text:
        return None, "empty_response"

    fence_pattern = re.compile(
        r"```(?:python|py)\s*\n(.*?)```",
        re.DOTALL | re.IGNORECASE,
    )
    blocks = fence_pattern.findall(text)
    if len(blocks) > 1:
        return None, "multiple_python_fences"
    if len(blocks) == 1:
        text = blocks[0].strip()
    elif text.startswith("```"):
        generic = re.findall(r"```\w*\s*\n(.*?)```", text, re.DOTALL)
        if len(generic) == 1:
            text = generic[0].strip()
        elif len(generic) > 1:
            return None, "multiple_code_fences"
        else:
            text = text.strip("`").strip()

    try:
        ast.parse(text)
    except SyntaxError as e:
        return None, str(e)
    return text, None