from datetime import datetime
from typing import cast

import discord
import pytest

from jg.chick.lib.threads import name_thread


DAYS = ["Pondělní", "Úterní", "Středeční", "Čtvrteční", "Páteční", "Sobotní", "Nedělní"]


class Message:
    def __init__(self, display_name: str, message: str):
        self.author = lambda: None
        self.author.display_name = display_name
        self.content = message


def test_name_thread_no_brackets():
    content = "Hello this is my thread"
    weekday = datetime.now().weekday()
    name_template = "{weekday} objev od {author}"
    expected_name = f"{DAYS[weekday]} objev od Jana"
    message = cast(discord.Message, Message("Jana", content))

    assert name_thread(message, name_template) == expected_name


@pytest.mark.parametrize(
    "content",
    [
        pytest.param("[ Hello this is my thread", id="brackets not closed"),
        pytest.param("[] Hello this is my thread", id="no text in brackets"),
        pytest.param("Hello this is my thread]", id="brackets not opened"),
    ],
)
def test_brackets_used_incorrectly(content: str):
    weekday = datetime.now().weekday()
    name_template = "{weekday} objev od {author}"
    expected_name = f"{DAYS[weekday]} objev od Jana"
    message = cast(discord.Message, Message("Jana", content))

    assert name_thread(message, name_template) == expected_name


def test_no_text_in_brackets():
    content = "[] Hello this is my thread"
    weekday = datetime.now().weekday()
    name_template = "{weekday} objev od {author}"
    expected_name = f"{DAYS[weekday]} objev od Jana"
    message = cast(discord.Message, Message("Jana", content))

    assert name_thread(message, name_template) == expected_name


@pytest.mark.parametrize(
    "content, expected_name",
    [
        pytest.param(
            "[eslint, nextjs]",
            "Objev od Jana: eslint, nextjs",
            id="comma separated strings with spaces",
        ),
        pytest.param(
            "[eslint,nextjs]",
            "Objev od Jana: eslint, nextjs",
            id="comma separated strings without spaces",
        ),
        pytest.param("[ Java ]", "Objev od Jana: Java", id="whitespaces around string"),
        pytest.param("[:css: CSS]", "Objev od Jana: :css: CSS", id="starting emoji"),
        pytest.param(
            "[eslint,nextjs, :css: CSS, ruby]",
            "Objev od Jana: eslint, nextjs, :css: CSS, ruby",
            id="emoji in the middle",
        ),
        pytest.param(
            "[ eslint ] Hello", "Objev od Jana: eslint", id="brackets at the beginning"
        ),
    ],
)
def test_parse_message_in_brackets(content: str, expected_name: str):
    message = cast(discord.Message, Message("Jana", content))
    name_template = "{weekday} objev od {author}"
    bracket_name_template = "Objev od {author}: {bracket_content}"

    assert (
        name_thread(message, name_template, bracket_name_template=bracket_name_template)
        == expected_name
    )
