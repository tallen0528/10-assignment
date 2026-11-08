"""auth.py - Account registration and login (passwords are salted + hashed, never stored in plain text)."""
import hashlib
import hmac
import os
import re

from ui import header, error, success, info, ask, ask_password

USERNAME_RE = re.compile(r"^[A-Za-z0-9_]{3,16}$")
MIN_PASSWORD = 6
MAX_LOGIN_ATTEMPTS = 3
PBKDF2_ROUNDS = 120_000


def hash_password(password, salt_hex):
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), PBKDF2_ROUNDS)
    return digest.hex()


class AuthManager:
    def __init__(self, db):
        self.db = db

    def register(self):
        """Create a new account. Returns the username, or None if the player cancelled."""
        header("Register")
        info("  Username: 3-16 letters, numbers or underscores. Leave blank to cancel.")
        while True:
            username = ask("  Choose a username: ")
            if not username:
                return None
            if not USERNAME_RE.match(username):
                error("  Invalid username. Use 3-16 letters, numbers or underscores (no spaces).")
            elif self.db.get_account(username):
                error("  That username is already taken. Try another.")
            else:
                break
        info(f"  Password: at least {MIN_PASSWORD} characters.")
        while True:
            password = ask_password("  Choose a password: ")
            if len(password) < MIN_PASSWORD:
                error(f"  Password too short (minimum {MIN_PASSWORD} characters).")
                continue
            if password != ask_password("  Repeat the password: "):
                error("  Passwords do not match. Try again.")
                continue
            break
        salt = os.urandom(16).hex()
        self.db.create_account(username, salt, hash_password(password, salt))
        success(f"  Account '{username}' created!")
        return username

    def login(self):
        """Log in an existing account. Returns the username, or None on cancel/too many failures."""
        header("Login")
        info("  Leave the username blank to cancel.")
        username = ask("  Username: ")
        if not username:
            return None
        account = self.db.get_account(username)
        for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
            password = ask_password("  Password: ")
            # Same message for unknown user / wrong password so usernames can't be probed.
            if account and hmac.compare_digest(hash_password(password, account["salt"]), account["hash"]):
                success(f"  Welcome back, {account['display_name']}!")
                return account["display_name"]
            left = MAX_LOGIN_ATTEMPTS - attempt
            error(f"  Wrong username or password. {left} attempt(s) left." if left else "  Too many failed attempts.")
        return None
