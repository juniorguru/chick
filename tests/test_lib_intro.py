import pytest
from textwrap import dedent

from juniorguru_chick.lib.intro import choose_intro_emojis, generate_intro_message


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


@pytest.mark.asyncio  # unfortunately ui.View() touches the event loop
async def test_generate_intro_message():

    message_content = """
        Mám takový obecný přehled o programování HTML, CSS,
        Bootstrap, Python, Matlab 🫣, SQL, okrajově JS. Teď na osobním projektu.
    """

    hello_snippet = (
        'Píp, píp! Tady kuře, místní robot. '
        'Vítej v klubu 👋'
        '\n\n'
        'Dík, že se představuješ! '
        'Když o tobě víme víc, můžeme ti líp radit <:meowthumbsup:842730599906279494>'
    )

    gh_connection_snippet = (
        '\n\n'
        'Vidím, že máš **profil na GitHubu**. Když si GitHub propojíš s Discordem, bude tvůj profil viditelnější. Do budoucna navíc chystáme pro lidi s propojeným GitHub profilem spoustu vychytávek <a:yayfrog:976193164471853097> '
        '\n\n'
        '1. Jdi do [nastavení](https://discord.com/channels/@me) '
        '\n'
        '2. Klikni na Propojení (_Connections_). '
        '\n'
        '3. Přidej GitHub. '
    )

    tips_snippet = (
        '\n\n'
        'Představení můžeš kdyžtak doplnit či změnit přes tři tečky a „Upravit zprávu“ 📝'
        '\n\n'
        # TODO https://github.com/juniorguru/juniorguru-chick/issues/12
        '- Nevíš co dál? Popiš svou situaci do <#788826407412170752>\n'
        '- Vybíráš kurz? Založ vlákno v <#1075052469303906335>\n'
        '- Hledáš konkrétní recenze? Zkus vyhledávání\n'
        '- Dotaz? Hurá do <#1067439203983568986>\n'
        '- Záznamy přednášek? <#788822884948770846>\n'
        '- Něco jiného? <#769966887055392768> snese cokoliv\n'
        '- Nevíš, jak to tady funguje? Ptej se v <#806215364379148348>'
    )

    footer_snippet = (
        '\n\n'
        'A nezapomeň, že junior.guru není jenom klub. '
        'Tady aspoň dva odkazy, které fakt nechceš minout: '
    )

    assert hello_snippet in generate_intro_message(message_content)["content"]
    assert tips_snippet in generate_intro_message(message_content)["content"]
    assert footer_snippet in generate_intro_message(message_content)["content"]

    assert gh_connection_snippet not in generate_intro_message(message_content)["content"]


@pytest.mark.asyncio  # unfortunately ui.View() touches the event loop
async def test_generate_intro_message_with_gh_connection_suggestion():
    message_content = """
        Mám takový obecný přehled o programování HTML, CSS,
        Bootstrap, Python, Matlab 🫣, SQL, okrajově JS.
        Můj Github je https://github.com/superghuser,
        ale pracuji teď na osobním projektu.
    """

    hello_snippet = (
        'Píp, píp! Tady kuře, místní robot. '
        'Vítej v klubu 👋'
        '\n\n'
        'Dík, že se představuješ! '
        'Když o tobě víme víc, můžeme ti líp radit <:meowthumbsup:842730599906279494>'
    )

    gh_connection_snippet = (
        '\n\n'
        'Vidím, že máš **profil na GitHubu**. Když si GitHub propojíš s Discordem, bude tvůj profil viditelnější. Do budoucna navíc chystáme pro lidi s propojeným GitHub profilem spoustu vychytávek <a:yayfrog:976193164471853097> '
        '\n\n'
        '1. Jdi do [nastavení](https://discord.com/channels/@me) '
        '\n'
        '2. Klikni na Propojení (_Connections_). '
        '\n'
        '3. Přidej GitHub. '
    )

    tips_snippet = (
        '\n\n'
        'Představení můžeš kdyžtak doplnit či změnit přes tři tečky a „Upravit zprávu“ 📝'
        '\n\n'
        # TODO https://github.com/juniorguru/juniorguru-chick/issues/12
        '- Nevíš co dál? Popiš svou situaci do <#788826407412170752>\n'
        '- Vybíráš kurz? Založ vlákno v <#1075052469303906335>\n'
        '- Hledáš konkrétní recenze? Zkus vyhledávání\n'
        '- Dotaz? Hurá do <#1067439203983568986>\n'
        '- Záznamy přednášek? <#788822884948770846>\n'
        '- Něco jiného? <#769966887055392768> snese cokoliv\n'
        '- Nevíš, jak to tady funguje? Ptej se v <#806215364379148348>'
    )

    footer_snippet = (
        '\n\n'
        'A nezapomeň, že junior.guru není jenom klub. '
        'Tady aspoň dva odkazy, které fakt nechceš minout: '
    )

    assert dedent(hello_snippet) in generate_intro_message(message_content)["content"]
    assert dedent(gh_connection_snippet) in generate_intro_message(message_content)["content"]
    assert dedent(tips_snippet) in generate_intro_message(message_content)["content"]
    assert dedent(footer_snippet) in generate_intro_message(message_content)["content"]
