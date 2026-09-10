#!/usr/bin/env python3
# =============================================================================
#  NAME:        stratopost.py
#
#  DESCRIPTION: A bot for posting quotes to bluesky.
#
#  VERSION:     v1.0d5
#
#  GITHUB:      https://github.com/r3v/stratopost
#
#  USAGE:
#               stratopost.py --botfile exampleBot.yaml
#               stratopost.py --botfile /home/user/exampleBot.yaml
#
# =============================================================================

import argparse
import os
import json
import random
import yaml
from datetime import datetime
from pathlib import Path
from atproto import Client, client_utils


# Config directory: XDG_CONFIG_HOME if set, else ~/.config
CONFIG_DIR = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "stratopost"

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Post a quote to Bluesky.")
parser.add_argument(
	"--botfile",
	dest="botfile",
	type=Path,
	required=True,
	help="Path to bot config YAML file",
)
args = parser.parse_args()

# Resolve botfile path (relative paths are resolved against CONFIG_DIR)
BOTFILE = args.botfile
if not BOTFILE.is_absolute():
	BOTFILE = CONFIG_DIR / BOTFILE

# Load bot configuration
with open(BOTFILE, "r") as f:
	config = yaml.safe_load(f)

# Resolve quote file path (relative paths are resolved against CONFIG_DIR)
QUOTE_FILE = Path(config["quote_file"])
if not QUOTE_FILE.is_absolute():
	QUOTE_FILE = CONFIG_DIR / QUOTE_FILE

BSKY_ACCOUNT_ENV = config["bsky_account_env"]
BSKY_APP_PASSWORD_ENV = config["bsky_app_password_env"]

# Retrieve bluesky account credentials from environment variables
BSKY_ACCOUNT = os.getenv(BSKY_ACCOUNT_ENV)
BSKY_APP_PASSWORD = os.getenv(BSKY_APP_PASSWORD_ENV)

# Authenticate
client = Client()
client.login(BSKY_ACCOUNT, BSKY_APP_PASSWORD)

# Select a quote from quotefile
with open(QUOTE_FILE, "r+") as f:
	quotes = json.load(f)

	if quotes["quotes"]:
		quote_to_post = random.choice(quotes["quotes"])

		# Build text to post # TODO: add hashtags
		text_builder = client_utils.TextBuilder()
		text_builder.text(quote_to_post["Quote_Text"])

		# Post!
		client.send_post(text_builder)

		# Update quote record
		quote_to_post["Post_Count"] = str(int(quote_to_post["Post_Count"]) + 1)
		quote_to_post["Last_Posted"] = datetime.now().strftime("%Y-%m-%d/%H:%M")

		# Write updated quotes back to file
		f.seek(0)
		json.dump(quotes, f, indent=2)
		f.truncate()
	else:
		print("No quotes available to post.")
