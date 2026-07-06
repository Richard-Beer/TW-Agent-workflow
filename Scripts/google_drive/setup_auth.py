"""
One-time OAuth 2.0 setup for the Google Drive utility.

Runs the installed-app OAuth flow using credentials.json (the OAuth client
secret downloaded from Google Cloud) and writes the resulting user credentials
to token.json. drive.py reads token.json on every run and refreshes it
automatically when it expires.

Usage:
  python -B setup_auth.py

A browser window opens for you to grant access. token.json is written next to
this script and is gitignored. Re-run this only if token.json is deleted or the
required scopes change.
"""

import os

from google_auth_oauthlib.flow import InstalledAppFlow

from drive import SCOPES, TOKEN_PATH

CREDENTIALS_PATH = os.path.join(os.path.dirname(__file__), 'credentials.json')


def main():
    if not os.path.exists(CREDENTIALS_PATH):
        raise FileNotFoundError(
            f"OAuth client secret not found: {CREDENTIALS_PATH}. "
            "Download it from the Google Cloud console and save it here."
        )
    flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_PATH, 'w') as f:
        f.write(creds.to_json())
    print(f"Authentication complete. Token written to {TOKEN_PATH}")


if __name__ == '__main__':
    main()
