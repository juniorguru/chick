import pytest

from jg.chick.lib.reviews import find_github_url, find_linkedin_url


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            """
                Ahojte, moc prosim o spatnu vazbu, ako na vas posobi moje CV- nizsie upravene, github a asi dam aj linkedin. diky moc

                https://github.com/PetraMic
                www.linkedin.com/in/petra-mičudová-0879a32a7
            """,
            "https://github.com/PetraMic/",
        ),
        (
            """
                Ahoj lidi, chtěl bych poprosit, pokud by si někdo našel čas a byl tak hodný a mohl mi dát zpětnou vazbu k CV, github a LinkedIn ?  s LinkedIn sem začal teprve nedávno takže tam myslím že bude hodně co vylepšit, ale nevím co přesně.

                www.linkedin.com/in/michal-lesák
                https://github.com/sirlestr
                Díky moc všem co si na to najdou prostor 🙂
            """,
            "https://github.com/sirlestr/",
        ),
        (
            """
                Ahoj, tak som si aktualizoval a vlastne dal dokopy moje CV....budem naozaj rad za vsetky rady a vopred dakujem kazdemu, kto sa na to pozrie 🙂

                Pripajam aj link na github https://github.com/Aberran
                linkedIn:
                https://www.linkedin.com/in/vladim%C3%ADr-%C5%A1ab%C3%ADk-787083267/
                ten bude este asi potrebovat aktualizaciu.
            """,
            "https://github.com/Aberran/",
        ),
    ],
)
def test_find_github_url(text: str, expected: str | None):
    assert find_github_url(text) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        (
            """
                Právě jsem si vypracovala životopis na LinkedIn
                https://www.linkedin.com/in/jana-b-o/

                Co mám dopilovat, prosím?
            """,
            "https://www.linkedin.com/in/jana-b-o/",
        ),
        (
            """
                Ahojte, moc prosim o spatnu vazbu, ako na vas posobi moje CV- nizsie upravene, github a asi dam aj linkedin. diky moc

                https://github.com/PetraMic
                www.linkedin.com/in/petra-mičudová-0879a32a7
            """,
            "https://www.linkedin.com/in/petra-mi%C4%8Dudov%C3%A1-0879a32a7/",
        ),
        (
            """
                Ahoj lidi, chtěl bych poprosit, pokud by si někdo našel čas a byl tak hodný a mohl mi dát zpětnou vazbu k CV, github a LinkedIn ?  s LinkedIn sem začal teprve nedávno takže tam myslím že bude hodně co vylepšit, ale nevím co přesně.

                www.linkedin.com/in/michal-lesák
                https://github.com/sirlestr
                Díky moc všem co si na to najdou prostor 🙂
            """,
            "https://www.linkedin.com/in/michal-les%C3%A1k/",
        ),
        (
            """
                Zdravím všechny,

                chtěl bych vás požádat o mrknutí se na moje CV, LinkedIn a pokud bude prostor tak i na moji portfolio stránku.

                LinkedIn - https://www.linkedin.com/in/jan-vincourek-68a441146/
                Portfolio - https://portfolio-vincourek.netlify.app/

                Děkuji.
            """,
            "https://www.linkedin.com/in/jan-vincourek-68a441146/",
        ),
        (
            """
                Ahoj, tak som si aktualizoval a vlastne dal dokopy moje CV....budem naozaj rad za vsetky rady a vopred dakujem kazdemu, kto sa na to pozrie 🙂

                Pripajam aj link na github https://github.com/Aberran
                linkedIn:
                https://www.linkedin.com/in/vladim%C3%ADr-%C5%A1ab%C3%ADk-787083267/
                ten bude este asi potrebovat aktualizaciu.
            """,
            "https://www.linkedin.com/in/vladim%C3%ADr-%C5%A1ab%C3%ADk-787083267/",
        ),
    ],
)
def test_find_linkedin_url(text: str, expected: str | None):
    assert find_linkedin_url(text) == expected
