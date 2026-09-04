"""Key-binding overrides for the Trutina interactive shell's prompt session.

Kept separate from loop.py because key bindings are interaction
behavior, not a themable visual -- unlike the banner and the
prompt/completion-menu colors (cli/shared/ui/), which could plausibly
be reused by some future non-shell surface, a Tab-acceptance override
is meaningful only in the context of this one PromptSession. It stays
in shell/ rather than cli/shared/ui/ for that reason.
"""

from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys


def build_key_bindings() -> KeyBindings:
    """Make Tab accept a match instead of cycling the menu selection.

    prompt_toolkit's default binding treats Tab, once a completion menu
    is already open, as "move to the next match" (the same as Down) --
    with complete_while_typing already keeping the menu open, this
    means Tab never actually completes anything, it just cycles. This
    override restores the expected "Tab completes the word" behavior:
    accept the currently highlighted match, or the first match if none
    is highlighted yet, and close the menu.
    """
    kb = KeyBindings()

    @kb.add(Keys.Tab)
    def _accept_completion(event) -> None:
        buffer = event.current_buffer
        state = buffer.complete_state

        if state is None:
            buffer.start_completion(select_first=True)
            return

        completion = state.current_completion
        if completion is None and state.completions:
            completion = state.completions[0]

        if completion is not None:
            buffer.apply_completion(completion)

    return kb
