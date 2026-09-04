from unittest.mock import MagicMock

import pytest
from prompt_toolkit.completion import Completion
from prompt_toolkit.keys import Keys
from trutina.cli.shell.keybindings import build_key_bindings


def _tab_handler():
    kb = build_key_bindings()
    for binding in kb.bindings:
        if binding.keys == (Keys.Tab,):
            return binding.handler
    raise AssertionError("No Tab binding was registered")


def _fake_event(buffer: MagicMock) -> MagicMock:
    event = MagicMock()
    event.current_buffer = buffer
    return event


@pytest.mark.unit
class TestTabKeyBinding:
    def test_opens_the_menu_when_no_completion_is_in_progress(self):
        handler = _tab_handler()
        buffer = MagicMock()
        buffer.complete_state = None

        handler(_fake_event(buffer))

        buffer.start_completion.assert_called_once_with(select_first=True)
        buffer.apply_completion.assert_not_called()

    def test_accepts_the_highlighted_completion(self):
        handler = _tab_handler()
        highlighted = Completion("account", start_position=0)

        state = MagicMock()
        state.current_completion = highlighted
        state.completions = [highlighted]
        buffer = MagicMock()
        buffer.complete_state = state

        handler(_fake_event(buffer))

        buffer.apply_completion.assert_called_once_with(highlighted)
        buffer.start_completion.assert_not_called()

    def test_accepts_the_first_completion_when_none_is_highlighted(self):
        handler = _tab_handler()
        first = Completion("account", start_position=0)
        second = Completion("journal", start_position=0)

        state = MagicMock()
        state.current_completion = None
        state.completions = [first, second]
        buffer = MagicMock()
        buffer.complete_state = state

        handler(_fake_event(buffer))

        buffer.apply_completion.assert_called_once_with(first)

    def test_does_nothing_when_completion_state_has_no_completions(self):
        state = MagicMock()
        state.current_completion = None
        state.completions = []
        buffer = MagicMock()
        buffer.complete_state = state

        handler = _tab_handler()
        handler(_fake_event(buffer))

        buffer.apply_completion.assert_not_called()
        buffer.start_completion.assert_not_called()
