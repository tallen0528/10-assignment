"""ui.py - Colours, text formatting helpers and validated terminal input.

Colour legend used across the whole game:
    green   = healing / healthy HP / consumables     bright yellow = gold
    cyan    = experience points                      bright blue   = NPCs
    red     = enemies, damage taken, danger          orange        = quests
    purple  = skills                                 magenta       = exits / quest items
"""
import getpass
import os
import sys
import textwrap
import time

if os.name == "nt":
    os.system("")  # makes ANSI colour codes work in the Windows console

USE_COLOR = "NO_COLOR" not in os.environ       # set NO_COLOR=1 to disable colours
FAST = bool(os.environ.get("RPG_FAST"))         # RPG_FAST=1 skips delays/pauses (used for testing)
WIDTH = 78
UNICODE = (getattr(sys.stdout, "encoding", None) or "").lower().replace("-", "").startswith("utf")


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    GRAY = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
    ORANGE = "\033[38;5;208m"     # quests
    PURPLE = "\033[38;5;177m"     # skills


def paint(text, *styles):
    """Wrap text in ANSI styles (no-op when colours are disabled)."""
    if not USE_COLOR or not styles:
        return str(text)
    return "".join(styles) + str(text) + C.RESET


# ---- semantic colour helpers -------------------------------------------------
def gold(n):          return paint(f"{n}g", C.BRIGHT_YELLOW, C.BOLD)
def xp(n):            return paint(f"{n} XP", C.BRIGHT_CYAN)
def npc_name(n):      return paint(n, C.BRIGHT_BLUE, C.BOLD)
def monster_name(n):  return paint(n, C.BRIGHT_RED, C.BOLD)
def skill_name(n):    return paint(n, C.PURPLE, C.BOLD)
def quest_text(t):    return paint(t, C.ORANGE)
def dealt(n):         return paint(n, C.BRIGHT_GREEN, C.BOLD)   # damage you deal
def taken(n):         return paint(n, C.BRIGHT_RED, C.BOLD)     # damage you take
def healed(n):        return paint(n, C.GREEN, C.BOLD)
def dim(t):           return paint(t, C.GRAY)


def info(text):       print(paint(text, C.GRAY))
def success(text):    print(paint(text, C.BRIGHT_GREEN))
def warn(text):       print(paint(text, C.YELLOW))
def error(text):      print(paint(text, C.BRIGHT_RED))


# ---- layout helpers ----------------------------------------------------------
def clear():
    if FAST:
        return
    os.system("cls" if os.name == "nt" else "clear")


def rule(char=None, color=C.GRAY):
    char = char or ("─" if UNICODE else "-")
    print(paint(char * WIDTH, color))


def header(text, color=C.BRIGHT_CYAN):
    line = ("═" if UNICODE else "=") * 3
    print(paint(f"{line} {text} {line}", color, C.BOLD))


def bar(cur, mx, width=20, color=None):
    """Coloured progress bar; defaults to a green/yellow/red HP bar."""
    ratio = 0.0 if mx <= 0 else max(0.0, min(1.0, cur / mx))
    filled = int(round(ratio * width))
    if color is None:
        color = C.GREEN if ratio > 0.6 else C.YELLOW if ratio > 0.3 else C.RED
    full, empty = ("█", "░") if UNICODE else ("#", "-")
    return paint(full * filled, color) + paint(empty * (width - filled), C.GRAY)


def say(name, text, color=C.BRIGHT_BLUE):
    """NPC dialogue: coloured name followed by wrapped, quoted speech."""
    lines = textwrap.wrap(f'"{text}"', width=max(30, WIDTH - len(name) - 2))
    pad = " " * (len(name) + 2)
    for i, line in enumerate(lines):
        print((paint(name, color, C.BOLD) + ": " if i == 0 else pad) + line)


def narrate(text, color=C.ITALIC, delay=0.012):
    """Story narration with an optional typewriter effect."""
    for line in textwrap.wrap(text, width=WIDTH):
        slow_print(paint(line, color), delay)


def slow_print(text, delay=0.01):
    if FAST or not sys.stdout.isatty():
        print(text)
        return
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def pause(msg="Press Enter to continue..."):
    if FAST:
        return
    input(paint(msg, C.GRAY))


# ---- validated input ---------------------------------------------------------
def ask(prompt="> "):
    """Read a stripped line of input (EOFError/KeyboardInterrupt bubble up to the game loop)."""
    return input(paint(prompt, C.BRIGHT_WHITE, C.BOLD)).strip()


def ask_int(prompt, lo, hi):
    """Keep asking until the player types an integer between lo and hi (inclusive)."""
    while True:
        raw = ask(prompt)
        try:
            value = int(raw)
        except ValueError:
            error(f"  '{raw}' is not a number - please type a number from {lo} to {hi}.")
            continue
        if lo <= value <= hi:
            return value
        error(f"  Please choose a number from {lo} to {hi}.")


def ask_choice(prompt, valid):
    """Keep asking until the (lower-cased) answer is in `valid`."""
    valid = [v.lower() for v in valid]
    while True:
        raw = ask(prompt).lower()
        if raw in valid:
            return raw
        error(f"  Invalid choice. Options: {', '.join(valid)}")


def ask_yes_no(prompt):
    while True:
        raw = ask(f"{prompt} (y/n): ").lower()
        if raw in ("y", "yes"):
            return True
        if raw in ("n", "no"):
            return False
        error("  Please answer 'y' or 'n'.")


def ask_password(prompt="Password: "):
    """Hidden password entry; falls back to normal input where getpass is unavailable."""
    if FAST:
        return input(prompt)
    try:
        return getpass.getpass(prompt)
    except (OSError, ValueError):
        return input(prompt)
