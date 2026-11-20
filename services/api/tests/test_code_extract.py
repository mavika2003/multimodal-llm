from app.llm.code_extract import extract_python_code


def test_plain_python():
    code, err = extract_python_code("print('hi')\n")
    assert err is None
    assert code == "print('hi')"


def test_fenced_python():
    raw = "Here you go:\n```python\nprint(1)\n```\n"
    code, err = extract_python_code(raw)
    assert err is None
    assert "print(1)" in code


def test_multiple_fences_rejected():
    raw = "```python\na=1\n```\n```python\nb=2\n```"
    code, err = extract_python_code(raw)
    assert code is None
    assert err == "multiple_python_fences"