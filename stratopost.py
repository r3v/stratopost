# =============================================================================
#  NAME:        stratopost.py
#
#  DESCRIPTION: A bot for posting quotes to bluesky.
#
#  VERSION:     v1.0d2
#
#  GITHUB:      https://github.com/r3v/stratopost
#
#  USAGE:
#               stratopost.py -botfile exampleBot.yaml
#               stratopost.py -botfile /home/user/exampleBot.yaml
#
# =============================================================================

import os
import json
import random
from atproto import Client, client_utils
from pathlib import Path


# Variables to edit
# TODO: Move to yaml file
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "stratopost"
QUOTE_FILE = CONFIG_DIR / "testQuotes.json"
BSKY_ACCOUNT_ENV = "STRATOPOST_ACCOUNT"
BSKY_APP_PASSWORD_ENV = "STRATOPOST_APP_PASSWORD"

# Retrieve bluesky account credentials from environment variables
BSKY_ACCOUNT = os.getenv(BSKY_ACCOUNT_ENV)
BSKY_APP_PASSWORD = os.getenv(BSKY_APP_PASSWORD_ENV)

# Authenticate
client = Client()
client.login(BSKY_ACCOUNT, BSKY_APP_PASSWORD)

# Select a quote from quotefile
with open(QUOTE_FILE, "r") as f:
	quotes = json.load(f)

if quotes["quotes"]:
	quote_to_post = random.choice(quotes["quotes"])
	
	# Build text to post # TODO: add hashtags
	text_builder = client_utils.TextBuilder()
	text_builder.text(quote_to_post["Quote_Text"])
	
	# Post!
	client.send_post(text_builder)
else:
	print("No quotes available to post.")
