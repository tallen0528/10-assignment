"""main.py - Entry point: title screen, login / registration menu, then the game.

Run with:  python main.py
"""
import sys

import story
from auth import AuthManager
from database import Database
from game import Game
from ui import C, paint, ask_int, error, info, pause


def main():
    try:
        db = Database()
    except Exception as exc:  # e.g. permissions problem
        error(f"Could not open the database: {exc}")
        return 1
    auth = AuthManager(db)

    try:
        while True:
            story.show_title()
            print("   1) Login")
            print("   2) Register a new account")
            print("   3) Quit")
            choice = ask_int("\n   > ", 1, 3)
            if choice == 3:
                break
            username = auth.login() if choice == 1 else auth.register()
            if not username:
                pause()
                continue
            try:
                Game(db, username).run()
            except Exception as exc:  # the game autosaves in its own `finally`
                error(f"\nSomething went wrong: {type(exc).__name__}: {exc}")
                info("Your progress was saved before the error. Log in again to continue.")
                pause()
    except (KeyboardInterrupt, EOFError):
        print()
    finally:
        db.close()
    print(paint("Thanks for playing. Farewell, hero!", C.BRIGHT_CYAN))
    return 0


if __name__ == "__main__":
    sys.exit(main())
