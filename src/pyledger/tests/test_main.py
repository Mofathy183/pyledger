"""Unit tests for main._run(), the CLI's single asyncio.run() entry point.

Protects the guarantee that CliContext is always released -- on the
success path and when the wrapped Typer dispatch raises, including via
SystemExit -- since this is the only place in the application permitted
to call asyncio.run() and therefore the only place that can guarantee
cleanup runs exactly once per invocation.
"""

import pytest

import pyledger.main as main_module


class _RecordingContext:
    """Minimal async-context-manager double standing in for CliContext.

    Tracks only how many times __aexit__ ran. The guarantee under test
    here is _run()'s own control flow (does cleanup always happen?), not
    CliContext-specific behavior -- that is covered separately in
    cli/tests/test_context.py. Using the real CliContext here would
    conflate the two and duplicate coverage.
    """

    def __init__(self) -> None:
        self.aclose_calls = 0

    async def __aenter__(self) -> _RecordingContext:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self.aclose_calls += 1


@pytest.mark.unit
class TestRunCleanup:
    async def test_closes_context_after_successful_dispatch(self, monkeypatch):
        context = _RecordingContext()
        monkeypatch.setattr(main_module, "build_context", lambda: context)
        monkeypatch.setattr(main_module, "app", lambda obj: None)

        await main_module._run()

        assert context.aclose_calls == 1

    async def test_closes_context_when_dispatch_raises(self, monkeypatch):
        context = _RecordingContext()

        def failing_app(obj):
            raise RuntimeError("command failed")

        monkeypatch.setattr(main_module, "build_context", lambda: context)
        monkeypatch.setattr(main_module, "app", failing_app)

        with pytest.raises(RuntimeError):
            await main_module._run()

        assert context.aclose_calls == 1

    async def test_closes_context_when_dispatch_exits(self, monkeypatch):
        """SystemExit does not inherit from Exception, so it is a distinct
        failure mode from the RuntimeError case above and worth covering
        explicitly -- Click uses SystemExit for its own normal exit path.
        """
        context = _RecordingContext()

        def exiting_app(obj):
            raise SystemExit(0)

        monkeypatch.setattr(main_module, "build_context", lambda: context)
        monkeypatch.setattr(main_module, "app", exiting_app)

        with pytest.raises(SystemExit):
            await main_module._run()

        assert context.aclose_calls == 1
