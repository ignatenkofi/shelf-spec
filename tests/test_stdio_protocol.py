"""End-to-end tests over the real stdio transport, with a real MCP client.

`test_server.py` drives the tools through ``mcp.call_tool`` in-process, which
covers validation and the JSON reply but never starts a server: no transport,
no ``serve`` subcommand, no serialization. "The module imports" has been
standing in for "a client can talk to it".

That gap is widest exactly when it costs most — a change to how the server is
declared, like the mcp 2.x port these tests were written for. Measured here:
breaking the `serve` path so the entry point starts nothing leaves the whole
in-process suite green.

The tools are spawned through ``shelf-spec serve``'s own code path
(``python -m shelf_spec serve``) rather than a private helper, so what the
tests exercise is what a client config launches.
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import sys
import time
from pathlib import Path

import pytest

pytest.importorskip("mcp", reason="the MCP client SDK is needed to drive the transport")

from mcp import ClientSession, StdioServerParameters  # noqa: E402
from mcp.client.stdio import stdio_client  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures"

# Generous on purpose: a flaky timeout would teach people to rerun the job,
# which is worse than the gap this file closes. Float seconds — mcp 2.x types
# the parameter that way and does not reject a leftover ``timedelta`` at the
# call site; it raises TypeError deep inside anyio on the first request.
WIRE_TIMEOUT = 60.0


def _flatten_exception(exc: BaseException) -> list[BaseException]:
    """Every exception in the tree: the group, its members, and their causes."""
    seen: list[BaseException] = []

    def walk(node: BaseException) -> None:
        if any(node is known for known in seen):
            return
        seen.append(node)
        for member in getattr(node, "exceptions", None) or ():
            walk(member)
        if node.__cause__ is not None:
            walk(node.__cause__)

    walk(exc)
    return seen


def _looks_like_timeout(exc: BaseException) -> bool:
    """True for "the wait ran out", whatever type the SDK wraps it in."""
    return isinstance(exc, TimeoutError) or "timed out" in str(exc).lower()


def _server() -> StdioServerParameters:
    return StdioServerParameters(
        command=sys.executable, args=["-m", "shelf_spec", "serve"], env=dict(os.environ)
    )


def _payload(result) -> dict:
    text = "".join(block.text for block in result.content if getattr(block, "text", None))
    return json.loads(text)


def _run(coro):
    return asyncio.run(coro)


def test_client_sees_the_three_tools_with_flat_schemas():
    """The roster and the flat-argument contract, as a client receives them.

    Flat input is a deliberate design choice here — clients get named
    arguments, not a nested ``params`` object — and it lives in the schema
    that travels over the wire, so it deserves an assertion on the far side of
    the transport and not only in-process.
    """

    async def scenario():
        async with stdio_client(_server()) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=WIRE_TIMEOUT) as session:
                await session.initialize()
                tools = {t.name: t for t in (await session.list_tools()).tools}

                assert set(tools) == {"shelf_init", "shelf_validate", "shelf_info"}
                for name, tool in tools.items():
                    properties = tool.input_schema["properties"]
                    assert "params" not in properties, f"{name} nests input under 'params'"
                    assert "shelf_path" in properties

    _run(scenario())


def test_validate_over_the_wire_answers_for_a_real_shelf(tmp_path: Path):
    """A call must reflect *this* shelf, not merely return well-formed JSON."""
    shelf = tmp_path / "memshelf_like"
    shutil.copytree(FIXTURES / "memshelf_like", shelf)

    async def scenario():
        async with stdio_client(_server()) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=WIRE_TIMEOUT) as session:
                await session.initialize()
                result = await session.call_tool("shelf_validate", {"shelf_path": str(shelf)})
                assert not result.is_error, result.content
                assert _payload(result)["verdict"] == "valid"

    _run(scenario())


def test_validate_over_the_wire_rejects_a_tree_that_is_not_a_shelf(tmp_path: Path):
    """Paired with the test above: a validator that says "valid" to everything
    would satisfy the happy path alone."""
    not_a_shelf = tmp_path / "empty"
    not_a_shelf.mkdir()

    async def scenario():
        async with stdio_client(_server()) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=WIRE_TIMEOUT) as session:
                await session.initialize()
                result = await session.call_tool("shelf_validate", {"shelf_path": str(not_a_shelf)})
                payload = _payload(result)
                assert payload["verdict"] != "valid", payload

    _run(scenario())


def test_a_server_that_never_answers_fails_instead_of_hanging():
    """The cap above must be load-bearing, not a comment.

    Asserted on the leaf exception naming a timeout rather than on "something
    was raised": a dead cap raises too, and elapsed time does not separate the
    cases — measured on the sibling ports, 2.02s dead against 4.03s live,
    because spawning the child dominates both.
    """
    silent = StdioServerParameters(
        command=sys.executable, args=["-c", "import time; time.sleep(3600)"]
    )
    started = time.monotonic()

    async def scenario():
        async with stdio_client(silent) as (read, write):
            async with ClientSession(read, write, read_timeout_seconds=2.0) as session:
                await session.initialize()

    with pytest.raises(BaseException) as caught:
        _run(scenario())
    elapsed = time.monotonic() - started

    raised = _flatten_exception(caught.value)
    assert not any(isinstance(exc, AssertionError) for exc in raised)
    assert any(_looks_like_timeout(exc) for exc in raised), (
        "nothing in the failure says the request timed out, so the cap was not "
        "what stopped it: " + "; ".join(f"{type(exc).__name__}: {exc}" for exc in raised)
    )
    assert elapsed < 60, f"waited {elapsed:.0f}s — the cap did not fire at all"
