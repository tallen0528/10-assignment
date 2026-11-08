"""story.py - Title banner, opening story and the ending."""
from ui import C, UNICODE, paint, narrate, pause, clear, slow_print

TITLE_LINES = ["", "T H E   S H A D O W   O V E R", "W I L L O W B R O O K", "", "a terminal role-playing adventure", ""]


def title_banner():
    """Boxed title built from text (Unicode box when the terminal supports it, plain ASCII otherwise)."""
    width = 46
    tl, tr, bl, br, h, v = ("╔", "╗", "╚", "╝", "═", "║") if UNICODE else ("+", "+", "+", "+", "-", "|")
    rows = [tl + h * width + tr]
    rows += [v + line.center(width) + v for line in TITLE_LINES]
    rows.append(bl + h * width + br)
    return "\n".join("   " + r for r in rows)

INTRO = [
    "For three hundred years the kingdom of Eldoria knew peace. Then the old crypts beneath the "
    "Ashen Hills cracked open, and the Lich King Morvath - a monarch who once cheated death - "
    "climbed out of the dark.",
    "His shadow crept across the land. Rivers turned black, the dead began to walk, and the "
    "beasts of the Whispering Forest grew wild and hungry. One by one the border villages fell silent.",
    "Willowbrook is the last village before the forest. Its people have barricaded their doors, "
    "lit their candles and waited for a hero. None came.",
    "Tonight, a lone traveler walks through the village gate with a rusty sword, a few coins and "
    "a name that nobody has heard of yet.",
]

ENDING = [
    "Morvath's crown cracks. The green fire in his eyes gutters, and the Lich King crumbles to "
    "ash that the Crypt's cold wind carries away.",
    "Across Eldoria the walking dead drop where they stand. Rivers clear. Birds return to the "
    "Whispering Forest, hesitantly at first, then in song.",
    "When you step out of the Crypt into daylight, Willowbrook's bells are ringing. Elder Alden "
    "waits at the gate with half the village behind him, weeping and laughing at once.",
    "You came as a stranger with a rusty sword. You return as the Hero of Willowbrook - and "
    "songs will be sung about you for three hundred years.",
]


def show_title():
    clear()
    print()
    print(paint(title_banner(), C.BRIGHT_CYAN, C.BOLD))


def show_intro(hero_name):
    clear()
    print(paint("\n  ~ PROLOGUE ~\n", C.BRIGHT_YELLOW, C.BOLD))
    for paragraph in INTRO:
        narrate(paragraph)
        print()
    narrate(f"Your name is {hero_name}. Eldoria's fate is in your hands.", C.BRIGHT_CYAN)
    print()
    pause()


def show_ending(hero_name):
    clear()
    print(paint("\n  ~ VICTORY ~\n", C.BRIGHT_YELLOW, C.BOLD))
    for paragraph in ENDING:
        narrate(paragraph)
        print()
    slow_print(paint(f"  THE END - {hero_name}, Hero of Willowbrook", C.BRIGHT_GREEN, C.BOLD), 0.03)
    print()
    pause()
