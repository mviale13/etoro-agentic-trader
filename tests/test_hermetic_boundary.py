"""The wire guard is enumerated from the code, not remembered.

`NETWORK_SEAMS` is a list of class names, and a list of names is only as
good as the memory of whoever last added a provider. It was wrong twice
by the time CI1 opened: `ArbitrumRpc` and `SubtensorRpc` were written
into `primary_sources.py` beside four guarded siblings and never added,
and the whole issuance reader was missing, which is how eight tests of a
payload's *shape* came to ask mempool.space whether it was up.

The conftest docstring already names the cost — *"adding one means
adding it here. The cost of forgetting is invisible"* — so this makes it
visible. The chain-surface module is enumerated rather than trusted, and
a new adapter fails here on the day it is written rather than on the day
someone else's host goes down.
"""

from __future__ import annotations

import ast
from pathlib import Path

from tests.conftest import NETWORK_SEAMS, SEAM_METHODS

#: The library calls that actually put bytes on the wire. Detected by
#: what a method *does* rather than by what it is called: CoinGecko's
#: `_get` is a pacing wrapper around `_request`, and a rule that guessed
#: from the name would have guarded the wrapper and missed the wire.
WIRE_CALLS = frozenset({"get", "post", "put", "patch", "delete", "request"})

#: Modules whose classes reach a keyless endpoint and are therefore
#: guarded wholesale. Keyed providers are silenced by `SETTINGS_READERS`
#: instead, which is a different failure mode with a different fix.
KEYLESS_MODULES = (
    Path("app/providers/primary_sources.py"),
    Path("app/providers/issuance_rule_provider.py"),
)


#: What constructing a client looks like, so a call on the thing it
#: returns counts as the wire too.
CLIENT_FACTORIES = frozenset({"Client", "Session", "AsyncClient"})


def _client_names(node: ast.AST) -> set[str]:
    """Names this body binds to a freshly constructed HTTP client.

    `with httpx.Client(...) as client:` and `client = httpx.Client(...)`
    are the same thing to a reader and were invisible to the rule below,
    which only recognised `httpx.get(...)` on the module itself. The
    first provider written the idiomatic way would have been enumerated
    as touching no wire at all — a guard silently guarding nothing, which
    is the failure this module exists to make loud.
    """

    bound: set[str] = set()

    def constructs(value: ast.AST) -> bool:
        return (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Attribute)
            and value.func.attr in CLIENT_FACTORIES
            and isinstance(value.func.value, ast.Name)
            and value.func.value.id in {"requests", "httpx"}
        )

    for inner in ast.walk(node):
        if isinstance(inner, ast.withitem):
            if constructs(inner.context_expr) and isinstance(
                inner.optional_vars, ast.Name
            ):
                bound.add(inner.optional_vars.id)

        if isinstance(inner, ast.Assign) and constructs(inner.value):
            for target in inner.targets:
                if isinstance(target, ast.Name):
                    bound.add(target.id)

    return bound


def _touches_the_wire(node: ast.AST) -> bool:
    """Whether this function body calls an HTTP library directly."""

    reaches = {"requests", "httpx"} | _client_names(node)

    for inner in ast.walk(node):
        if not isinstance(inner, ast.Call):
            continue

        call = inner.func

        if (
            isinstance(call, ast.Attribute)
            and call.attr in WIRE_CALLS
            and isinstance(call.value, ast.Name)
            and call.value.id in reaches
        ):
            return True

    return False


def wire_classes(module: Path) -> dict[str, tuple[str, ...]]:
    """Every class in the module that talks to the wire, and how."""

    tree = ast.parse(module.read_text(encoding="utf-8"))

    found = {}

    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue

        methods = tuple(
            sorted(
                child.name
                for child in node.body
                if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef)
                and _touches_the_wire(child)
            )
        )

        if methods:
            found[node.name] = methods

    return found


def test_every_keyless_wire_class_is_guarded() -> None:
    """A chain adapter with no seam entry would run live in the suite."""

    unguarded = []

    for module in KEYLESS_MODULES:
        dotted = str(module.with_suffix("")).replace("/", ".")

        for name in wire_classes(module):
            if f"{dotted}.{name}" not in NETWORK_SEAMS:
                unguarded.append(f"{dotted}.{name}")

    assert not unguarded, (
        "these classes reach a keyless endpoint and no NETWORK_SEAMS entry "
        f"blocks them: {sorted(unguarded)}"
    )


def test_every_guarded_class_has_all_its_wire_methods_named() -> None:
    """Naming one method of a two-protocol adapter guards half of it.

    The issuance reader is the live example: a REST `_get` for Bitcoin's
    tip and a JSON-RPC `_rpc` for Solana's inflation. Blocking only the
    first would have left Solana's schedule reachable, and the suite
    would have looked fixed.
    """

    missing = []

    for module in KEYLESS_MODULES:
        dotted = str(module.with_suffix("")).replace("/", ".")

        for name, methods in wire_classes(module).items():
            seam = f"{dotted}.{name}"

            if seam not in SEAM_METHODS:
                continue

            for method in methods:
                if method not in SEAM_METHODS[seam]:
                    missing.append(f"{seam}.{method}")

    assert not missing, f"wire methods reachable past the guard: {sorted(missing)}"


def test_every_named_seam_still_exists() -> None:
    """A renamed adapter must not leave a guard silently guarding nothing."""

    for seam, methods in SEAM_METHODS.items():
        module_path = Path(seam.rsplit(".", 1)[0].replace(".", "/") + ".py")
        name = seam.rsplit(".", 1)[1]

        classes = wire_classes(module_path)

        assert name in classes, f"{seam} names a class that no longer exists"

        for method in methods:
            assert method in classes[name], f"{seam}.{method} no longer exists"
