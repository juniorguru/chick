import pytest
from juniorguru_chick.lib.intro import choose_intro_emojis


def test_choose_intro_emojis():
    message_content = """
        Mám takový obecný přehled o programování HTML, CSS,
        Bootstrap, Python, Matlab 🫣, SQL, okrajově JS.
    """

    assert '<:python:842331892091322389>' in choose_intro_emojis(message_content)


@pytest.mark.parametrize('message_content, expected_emoji', [
    ('základní struktury v pythonu a C# v ITnetwork', '<:csharp:842666113230045224>'),
    ('Láká mě C++ a C#', '<:cpp:842666129071931433>'),
])
def test_choose_intro_emoji_edge_cases(message_content, expected_emoji):
    assert expected_emoji in choose_intro_emojis(message_content)
