from post_processor import post_process


def test_punctuation_commands():
    assert post_process("Hej komma det fungerar punkt") == "Hej, det fungerar."
    assert post_process("Bra jobbat utropstecken") == "Bra jobbat!"
    assert post_process("Vad händer frågetecken") == "Vad händer?"


def test_line_break_commands():
    assert post_process("Rad ett ny rad rad två") == "Rad ett\nrad två"
    assert post_process("Första nytt stycke andra") == "Första\n\nandra"


def test_spacing_cleanup():
    assert post_process("Hej komma  där") == "Hej, där"


def test_command_words_swallow_whisper_punctuation():
    assert post_process("Det fungerar utropstecken, här") == "Det fungerar! här"
    assert post_process("Fungerar det frågetecken.") == "Fungerar det?"
    assert post_process("Slut punkt.") == "Slut."


def test_literal_command_words_in_examples():
    text = (
        "Så nu ska det faktiskt funka att använda saker som utropstecken, "
        "ny rad, och sedan fortsätta skriva frågetecken."
    )
    assert post_process(text) == text
