import pytest

from jg.chick.lib.intro import choose_intro_emojis, generate_intro_message


def test_choose_intro_emojis():
    user_message_content = """
        Mám takový obecný přehled o programování HTML, CSS,
        Bootstrap, Python, Matlab 🫣, SQL, okrajově JS.
    """

    assert "<:python:842331892091322389>" in choose_intro_emojis(user_message_content)


@pytest.mark.parametrize(
    "user_message_content, expected_emoji",
    [
        (
            "základní struktury v pythonu a C# v ITnetwork",
            "<:csharp:842666113230045224>",
        ),
        ("Láká mě C++ a C#", "<:cpp:842666129071931433>"),
    ],
)
def test_choose_intro_emoji_edge_cases(user_message_content: str, expected_emoji: str):
    assert expected_emoji in choose_intro_emojis(user_message_content)


@pytest.mark.asyncio  # unfortunately ui.View() touches the event loop
async def test_generate_intro_message():
    user_message_content = """
        Mám takový obecný přehled o programování HTML, CSS,
        Bootstrap, Python, Matlab 🫣, SQL, okrajově JS. Teď na osobním projektu.
    """
    hello_snippet = "Píp, píp! Tady kuře, místní robot"
    gh_connection_snippet = "Vidím, že máš **profil na GitHubu**"
    tips_snippet = "Představení můžeš kdyžtak doplnit či změnit"
    footer_snippet = "A nezapomeň, že junior.guru není jenom klub"
    bot_message_content = generate_intro_message(user_message_content)["content"]

    assert hello_snippet in bot_message_content
    assert tips_snippet in bot_message_content
    assert footer_snippet in bot_message_content
    assert gh_connection_snippet not in bot_message_content


@pytest.mark.asyncio  # unfortunately ui.View() touches the event loop
async def test_generate_intro_message_with_gh_connection_suggestion():
    user_message_content = """
        Mám takový obecný přehled o programování HTML, CSS,
        Bootstrap, Python, Matlab 🫣, SQL, okrajově JS.
        Můj Github je https://github.com/superghuser,
        ale pracuji teď na osobním projektu.
    """
    hello_snippet = "Píp, píp! Tady kuře, místní robot"
    gh_connection_snippet = "Vidím, že máš **profil na GitHubu**"
    tips_snippet = "Představení můžeš kdyžtak doplnit či změnit"
    footer_snippet = "A nezapomeň, že junior.guru není jenom klub"
    bot_message_content = generate_intro_message(user_message_content)["content"]

    assert hello_snippet in bot_message_content
    assert gh_connection_snippet in bot_message_content
    assert tips_snippet in bot_message_content
    assert footer_snippet in bot_message_content


@pytest.mark.parametrize(
    "user_message_content, expected_emoji",
    [
        ("Zkouším MySQL", "<:database:900833211809136641>"),
        ("Zkouším MongoDB", "<:database:900833211809136641>"),
        ("Zkouším PostgreSQL", "<:database:900833211809136641>"),
        ("Zkouším Kubernetes", "<:docker:842465373911777290>"),
        ("Zkouším Flask", "<:python:842331892091322389>"),
        ("Zkouším pandas", "<:python:842331892091322389>"),
        ("Zkouším Next.js", "<:react:842332165822742539>"),
        ("Zkouším Angular", "<:typescript:842332083605995541>"),
        ("Zkouším Bootstrap", "<:css:842343369618751519>"),
        ("Zkouším Tailwind", "<:css:842343369618751519>"),
    ],
)
def test_choose_intro_emojis_fallbacks(user_message_content: str, expected_emoji: str):
    assert expected_emoji in choose_intro_emojis(user_message_content)
