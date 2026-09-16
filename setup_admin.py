"""Provision the Chemini AI administrator account locally.

This is a deployment/setup utility, not a public registration feature.
Run it from the project directory once before using /admin/login.
"""

import os
import secrets
from getpass import getpass

from dotenv import load_dotenv, set_key
from werkzeug.security import generate_password_hash

ENV_FILE = ".env"


def main():
    load_dotenv(ENV_FILE)

    print("\nChemini AI — Admin Provisioning")
    print("This creates/updates the server-side admin credentials in .env.")
    print("It does not create a public registration page.\n")

    username = input("Admin ID [admin]: ").strip() or "admin"
    if len(username) < 3 or len(username) > 120:
        raise SystemExit("Admin ID must be between 3 and 120 characters.")

    password = getpass("Admin password: ")
    confirmation = getpass("Confirm admin password: ")

    if not password:
        raise SystemExit("Password cannot be empty.")

    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    secret_key = os.getenv("SECRET_KEY") or secrets.token_urlsafe(48)
    password_hash = generate_password_hash(password, method="scrypt")
    recovery_key = secrets.token_urlsafe(32)

    set_key(ENV_FILE, "SECRET_KEY", secret_key)
    set_key(ENV_FILE, "ADMIN_USERNAME", username)
    set_key(ENV_FILE, "ADMIN_PASSWORD_HASH", password_hash)
    set_key(ENV_FILE, "ADMIN_RESET_TOKEN", recovery_key)
    set_key(ENV_FILE, "SESSION_COOKIE_SECURE", os.getenv("SESSION_COOKIE_SECURE", "0"))

    print("\nAdmin configuration saved successfully.")
    print("\nIMPORTANT: Save this recovery key somewhere secure. It is required to reset the admin password:")
    print(f"\n    {recovery_key}\n")
    print("Restart the Flask application before logging in.")
    print("Open /admin/login and use the credentials you just configured.\n")


if __name__ == "__main__":
    main()
