"""What a module can *reach*, as opposed to what it mentions.

Every import-graph guard on this platform needs the same thing, and
three suites each wrote it separately before this file existed. The
reason it keeps being needed is worth stating once, because a fourth
suite will need it too:

**A module that explains what it refuses will fail a text search for the
thing it refuses.** `market_peer_group` says in as many words that it
must not see an archetype. `crypto_quality` says it will not read
`CompanyFacts.circulating_supply`. `mechanical_issuance` says it scores
nothing and bands nothing. A guard grepping for "archetype", for
"circulating_supply" or for "band" forbids all three from documenting
their own boundary — which is the opposite of what the guard is for.

So a guard asks the parse tree: names, attributes, imports, arguments
and definitions. Docstrings and prose are not reachable, and neither is
a comment.

`with_literals` adds string constants, for the guards that need to catch
a literal-keyed lookup — `row["holder_revenue"]` reaches something a
name-only scan would miss. It still excludes docstrings.
"""

from __future__ import annotations

import ast
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent


def reachable(module: str, with_literals: bool = False) -> str:
    """The identifiers a module can reach, newline-joined and folded.

    `module` is a repository-relative path — "app/domain/thing.py" — so
    a guard names the file it is guarding rather than an import path
    that may not resolve.
    """

    tree = ast.parse((ROOT / module).read_text(encoding="utf-8"))

    docstrings = {
        ast.get_docstring(node, clean=False)
        for node in ast.walk(tree)
        if isinstance(
            node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        )
    }

    words: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            words.append(node.id)
        elif isinstance(node, ast.Attribute):
            words.append(node.attr)
        elif isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            words.append(node.name)
        elif isinstance(node, ast.alias):
            words.append(f"{node.name} {node.asname or ''}")
        elif isinstance(node, ast.ImportFrom):
            words.append(node.module or "")
        elif isinstance(node, ast.arg):
            words.append(node.arg)
        elif with_literals and isinstance(node, ast.Constant):
            if isinstance(node.value, str) and node.value not in docstrings:
                words.append(node.value)

    return "\n".join(words).casefold()
