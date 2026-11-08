"""database.py - TinyDB storage for user accounts and game progress.

Two tables live in one JSON file (data/rpg_db.json):
    accounts - username, salted password hash, creation time
    saves    - one document per user holding the complete player state
"""
import json
import os
import time

from tinydb import TinyDB, Query

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "rpg_db.json")


class Database:
    def __init__(self, path=None):
        self.path = path or DEFAULT_PATH
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        try:
            self.db = TinyDB(self.path, indent=2)
        except json.JSONDecodeError:
            # A damaged file would block every login - keep a backup and start fresh.
            backup = f"{self.path}.corrupt-{int(time.time())}"
            os.replace(self.path, backup)
            print(f"Warning: database file was unreadable; moved to {backup} and created a new one.")
            self.db = TinyDB(self.path, indent=2)
        self.accounts = self.db.table("accounts")
        self.saves = self.db.table("saves")

    # ---- accounts ------------------------------------------------------------
    def get_account(self, username):
        return self.accounts.get(Query().username == username.lower())

    def create_account(self, username, salt, pw_hash):
        self.accounts.insert({
            "username": username.lower(),
            "display_name": username,
            "salt": salt,
            "hash": pw_hash,
            "created": time.strftime("%Y-%m-%d %H:%M:%S"),
        })

    # ---- game saves ----------------------------------------------------------
    def save_game(self, username, data):
        record = {"username": username.lower(), "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"), "player": data}
        cond = Query().username == username.lower()
        if self.saves.get(cond):
            self.saves.update(record, cond)
        else:
            self.saves.insert(record)

    def load_game(self, username):
        record = self.saves.get(Query().username == username.lower())
        return record["player"] if record else None

    def has_save(self, username):
        return self.saves.get(Query().username == username.lower()) is not None

    def delete_save(self, username):
        self.saves.remove(Query().username == username.lower())

    def close(self):
        self.db.close()
