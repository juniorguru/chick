"""Introduction handling for new members in the #ahoj channel.

This module provides functionality for welcoming new members to the Discord server,
including emoji selection based on mentioned technologies and generating
personalized welcome messages.
"""

import re
from textwrap import dedent
from typing import Any

from discord import ButtonStyle, ui

PATTERNS_EMOJIS_MAPPING = {
    re.compile(r"\bpython\w*\b", re.I): [
        "<:python:842331892091322389>",
    ],
    re.compile(r"\bsql\b", re.I): [
        "<:database:900833211809136641>",
    ],
    re.compile(r"\bphp\b", re.I): [
        "<:php:842331754731274240>",
    ],
    re.compile(r"\b(nette|laravel|symfony)\w*\b", re.I): [
        "<:php:842331754731274240>",
    ],
    re.compile(r"\bmysql\b", re.I): [
        "<:mysql:1036337592582541314>",
    ],
    re.compile(r"\bmongo\w*\b", re.I): [
        "<:mongodb:976200776118583348>",
    ],
    re.compile(r"\bpostgre\w+\b", re.I): [
        "<:postgresql:900831229971169350>",
    ],
    re.compile(r"\bkubernet\w*\b", re.I): [
        "<:kubernetes:976200847014899742>",
    ],
    re.compile(r"\bdocker\w*\b", re.I): [
        "<:docker:842465373911777290>",
    ],
    re.compile(r"\blinux\w*\b", re.I): [
        "<:tux:842343455845515264>",
    ],
    re.compile(r"\bswift\w*\b", re.I): [
        "<:swift:900831808814473266>",
    ],
    re.compile(r"\bdjang\w+\b", re.I): [
        "<:django:844534232297504779>",
    ],
    re.compile(r"\bflask\w*\b", re.I): [
        "<:flask:1166303630001975367>",
    ],
    re.compile(r"\bpandas\b", re.I): [
        "<:pandas:844567908688461854>",
    ],
    re.compile(r"\bexcel\w*\b", re.I): [
        "<:excel:960457644504674314>",
    ],
    re.compile(r"\bpower ?bi\b", re.I): [
        "<:powerbi:960457607745794119>",
    ],
    re.compile(r"\bdatab(aá)ze\b"): [
        "<:database:900833211809136641>",
    ],
    re.compile(r"\bjavascript\w*\b", re.I): [
        "<:javascript:842329110293381142>",
    ],
    re.compile(r"\bJS\b"): [
        "<:javascript:842329110293381142>",
    ],
    re.compile(r"\btypescript\w*\b", re.I): [
        "<:typescript:842332083605995541>",
    ],
    re.compile(r"\bTS\b"): [
        "<:typescript:842332083605995541>",
    ],
    re.compile(r"\bHTML\b"): [
        "<:html:842343387964375050>",
    ],
    re.compile(r"\bCSS\b"): [
        "<:css:842343369618751519>",
    ],
    re.compile(r"\bfront\-?end\w*\b", re.I): [
        "<:html:842343387964375050>",
        "<:css:842343369618751519>",
        "<:javascript:842329110293381142>",
    ],
    re.compile(r"\bbootstrap\w*\b", re.I): [
        "<:bootstrap:900834695422545940>",
        "<:css:842343369618751519>",
    ],
    re.compile(r"\btailwind\w*\b", re.I): [
        "<:tailwind:900834412248309770>",
        "<:css:842343369618751519>",
    ],
    re.compile(r"\bC\#\W"): [
        "<:csharp:842666113230045224>",
    ],
    re.compile(r"\b\.NET\b", re.I): [
        "<:csharp:842666113230045224>",
    ],
    re.compile(r"\b(java|javy|javě|javu|javou)\b", re.I): [
        "<:java:1036333651740327966>"
    ],
    re.compile(r"\bkotlin\w*\b", re.I): [
        "<:kotlin:1001234560056578149>",
    ],
    re.compile(r"\bC\+\+\W"): [
        "<:cpp:842666129071931433>",
    ],
    re.compile(r"\breact\w*\b", re.I): [
        "<:react:842332165822742539>",
    ],
    re.compile(r"\bvue\b", re.I): [
        "<:vue:842332056138416168>",
    ],
    re.compile(r"\bangular\w*\b", re.I): [
        "<:angular:844527194730266694>",
    ],
    re.compile(r"\bnext\.?js\b", re.I): [
        "<:nextjs:963799617886121994>",
    ],
    re.compile(r"\bAPI\b"): [
        "<:api:900833604303732766>",
    ],
}


def choose_intro_emojis(intro_message_content: str) -> list[str]:
    """Select emoji reactions based on technologies mentioned in an introduction.

    Analyzes the message content for technology keywords (Python, JavaScript,
    Docker, etc.) and returns matching emoji reactions.

    Args:
        intro_message_content: The text of the user's introduction message.

    Returns:
        List of emoji strings starting with default welcome emojis,
        followed by technology-specific emojis.
    """
    emojis = set()
    for pattern_re, pattern_emojis in PATTERNS_EMOJIS_MAPPING.items():
        if pattern_re.search(intro_message_content):
            emojis.update(pattern_emojis)
    return ["👋", "🐣", "👍"] + list(emojis)


def generate_intro_message(intro_message_content: str) -> dict[str, Any]:
    """Generate a personalized welcome message for a new member.

    Creates a welcome message with helpful tips and links. If the user
    mentions a GitHub profile in their introduction, includes a suggestion
    to get it reviewed.

    Args:
        intro_message_content: The text of the user's introduction message.

    Returns:
        Dictionary with 'content' (str) and 'view' (ui.View) keys,
        ready to be unpacked into thread.send().
    """
    greeting = (
        "Píp, píp! Tady kuře, místní robot. "
        "Vítej v klubu 👋"
        "\n\n"
        "Dík, že se představuješ! "
        "Když o tobě víme víc, můžeme ti líp radit <:meowthumbsup:842730599906279494>"
    )
    tips = (
        "\n\n"
        "Představení můžeš kdyžtak doplnit či změnit přes tři tečky a „Upravit zprávu“ 📝"
        "\n\n"
        # TODO https://github.com/juniorguru/juniorguru-chick/issues/12
        "- Nevíš co dál? Popiš svou situaci do <#788826407412170752>\n"
        "- Vybíráš kurz? Založ vlákno v <#1075052469303906335>\n"
        "- Hledáš konkrétní recenze? Zkus vyhledávání\n"
        "- Dotaz? Hurá do <#1067439203983568986>\n"
        "- Záznamy přednášek? <#1169636415387205632>\n"
        "- Něco jiného? <#769966887055392768> snese cokoliv\n"
        "- Nevíš, jak to tady funguje? Ptej se v <#806215364379148348>"
    )
    gh_connection_snippet = (
        "\n\n"
        "Vidím, že máš **profil na GitHubu**. "
        "Hoď ho do <#1123527619716055040> a dám ti na něj zpětnou vazbu. "
        "Možná si už můžeš hledat práci přes [junior.guru/candidates](https://junior.guru/candidates/)?"
        "<a:awkward:985064290044223488>"
    )
    footer = (
        "\n\n"
        "A nezapomeň, že junior.guru není jenom klub. "
        "Tady aspoň dva odkazy, které fakt nechceš minout: "
    )

    # Compose the greeting message depending on the intro message content
    content = greeting
    if "github.com/" in intro_message_content:
        content = content + gh_connection_snippet
    content = content + tips + footer
    content = dedent(content)

    view = ui.View(
        ui.Button(
            emoji="📖",
            label="Příručka",
            url="https://junior.guru/handbook/",
            style=ButtonStyle.secondary,
        ),
        ui.Button(
            emoji="💌",
            label="Newsletter",
            url="https://junior.guru/news/",
            style=ButtonStyle.secondary,
        ),
    )
    return dict(content=content, view=view)
