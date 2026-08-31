import pytest
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document
from trutina.cli.shell_completion import build_completer


def _complete(completer, text: str) -> set[str]:
    return {c.text for c in completer.get_completions(Document(text), CompleteEvent())}


@pytest.mark.unit
class TestBuildCompleter:
    def test_completes_top_level_group_names(self):
        completer = build_completer()

        assert _complete(completer, "ac") == {"account"}
        assert _complete(completer, "jour") == {"journal"}
        assert _complete(completer, "post") == {"posting"}

    def test_completes_account_subcommands(self):
        completer = build_completer()

        assert _complete(completer, "account ") == {
            "create",
            "get",
            "list",
            "update",
            "delete",
        }

    def test_completes_journal_subcommands(self):
        completer = build_completer()

        assert _complete(completer, "journal ") == {"create", "get", "list"}

    def test_completes_posting_subcommands(self):
        completer = build_completer()

        assert _complete(completer, "posting ") == {
            "post",
            "get-by-account",
            "get-by-journal",
        }


@pytest.mark.unit
class TestSlashPrefixCompletion:
    def test_slash_prefixed_group_completion_matches_bare(self):
        completer = build_completer()

        assert _complete(completer, "ac") == _complete(completer, "/ac")

    def test_slash_prefixed_subcommand_completion_matches_bare(self):
        completer = build_completer()

        assert _complete(completer, "account ") == _complete(completer, "/account ")


@pytest.mark.unit
class TestCompletionDescriptions:
    def test_group_completions_carry_description(self):
        completer = build_completer()
        completions = list(completer.get_completions(Document("ac"), CompleteEvent()))

        assert completions[0].display_meta_text == "Manage the chart of accounts."

    def test_subcommand_completions_carry_description(self):
        completer = build_completer()
        completions = list(
            completer.get_completions(Document("posting "), CompleteEvent())
        )

        by_name = {c.text: c.display_meta_text for c in completions}
        assert by_name["post"].startswith("Post a journal entry")


@pytest.mark.unit
class TestBuiltinCompletion:
    def test_completes_exit_and_quit(self):
        completer = build_completer()
        assert _complete(completer, "ex") == {"exit"}
        assert _complete(completer, "qu") == {"quit"}

    def test_builtin_completions_carry_description(self):
        completer = build_completer()
        completions = list(completer.get_completions(Document("exi"), CompleteEvent()))
        assert completions[0].display_meta_text == "Leave the interactive shell."

    def test_slash_prefixed_builtin_matches_bare(self):
        completer = build_completer()
        assert _complete(completer, "exit") == _complete(completer, "/exit")
