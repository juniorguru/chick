from juniorguru_chick.bot import choose_intro_emojis


def test_choose_intro_emojis():
    message_content = """
        Mám takový obecný přehled o programování HTML, CSS,
        Bootstrap, Python, Matlab 🫣, SQL, okrajově JS.
    """

    assert '<:python:842331892091322389>' in choose_intro_emojis(message_content)
