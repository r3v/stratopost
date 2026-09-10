#!/usr/bin/env python3
# =============================================================================
#  NAME:        stratopost.py
#
#  DESCRIPTION: A bot for posting quotes to bluesky.
#
#  VERSION:     v1.0d7
#
#  GITHUB:      https://github.com/r3v/stratopost
#
#  USAGE:
#               stratopost.py --botfile exampleBot.yaml
#               stratopost.py --botfile exampleBot.yaml --dry-run
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


# Keys expected in the botfile yaml (see exampleBot.yaml)
EXPECTED_BOTFILE_KEYS = [
	"Bot_Name",
	"Bsky_Account_Env",
	"Bsky_App_Password_Env",
	"Quote_File",
	"Post_Hashtags",
	"Post_Length_Limit",
	"Days_Till_Repeat",
	"Log_Level",
	"Log_File",
]

# Keys expected in each quote record in the quote json file
EXPECTED_QUOTE_KEYS = ["Quote_Text", "Quote_Length", "Post_Count", "Last_Posted"]

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
parser.add_argument(
	"--dry-run",
	dest="dryrun",
	action="store_true",
	help="Run all checks and select a quote, but do not post.",
)
args = parser.parse_args()

# Resolve botfile path (relative paths are resolved against CONFIG_DIR)
BOTFILE = args.botfile
if not BOTFILE.is_absolute():
	BOTFILE = CONFIG_DIR / BOTFILE

# Load bot configuration
config = {}
load_error = None
try:
	with open(BOTFILE, "r") as f:
		config = yaml.safe_load(f) or {}
except (OSError, yaml.YAMLError) as e:
	if not args.dryrun:
		raise
	load_error = str(e)

# Fall back to a generic name if the botfile couldn't be read
BOT_NAME = config.get("Bot_Name", "stratopost")

if args.dryrun:
	print(f"{BOT_NAME} dry run. (No posts will be made or files updated.)")

	if load_error:
		print(f"Settings file check: Fail {BOTFILE}\n({load_error})")
		raise SystemExit(1)

	missing_keys = [key for key in EXPECTED_BOTFILE_KEYS if key not in config]
	if missing_keys:
		print(f"Settings file check: Fail {BOTFILE}\n(missing key(s): {', '.join(missing_keys)})")
		raise SystemExit(1)

	print(f"Settings file check: Pass {BOTFILE}")

# Resolve quote file path (relative paths are resolved against CONFIG_DIR)
QUOTE_FILE = Path(config["Quote_File"])
if not QUOTE_FILE.is_absolute():
	QUOTE_FILE = CONFIG_DIR / QUOTE_FILE

BSKY_ACCOUNT_ENV = config["Bsky_Account_Env"]
BSKY_APP_PASSWORD_ENV = config["Bsky_App_Password_Env"]

# Retrieve bluesky account credentials from environment variables
BSKY_ACCOUNT = os.getenv(BSKY_ACCOUNT_ENV)
BSKY_APP_PASSWORD = os.getenv(BSKY_APP_PASSWORD_ENV)

# Authenticate
client = Client()
try:
	client.login(BSKY_ACCOUNT, BSKY_APP_PASSWORD)
except Exception as e:
	if args.dryrun:
		print(f"Bluesky credentials check: Fail\n({e})")
		raise SystemExit(1)
	raise

if args.dryrun:
	print("Bluesky credentials check: Pass")

# Select a quote from quotefile
try:
	with open(QUOTE_FILE, "r+") as f:
		quotes = json.load(f)

		quote_list = quotes.get("quotes")
		if not isinstance(quote_list, list) or not quote_list:
			raise ValueError("no usable 'quotes' list found")

		for record in quote_list:
			missing = [key for key in EXPECTED_QUOTE_KEYS if key not in record]
			if missing:
				raise ValueError(f"quote record missing key(s): {', '.join(missing)}")

		quote_to_post = random.choice(quote_list)

		if args.dryrun:
			print(f"Quote file check: Pass {QUOTE_FILE}")
			print(f'Quote selected: "{quote_to_post["Quote_Text"]}"')
			print(f"Quote last posted: {quote_to_post['Last_Posted']}")
			print(f"Quote count: {quote_to_post['Post_Count']}")
			print()
		else:
			# Build text to post # TODO: add hashtags
			text_builder = client_utils.TextBuilder()
			text_builder.text(quote_to_post["Quote_Text"])

			# Post!
			client.send_post(text_builder)

			# Update quote metadata
			quote_to_post["Post_Count"] = str(int(quote_to_post["Post_Count"]) + 1)
			quote_to_post["Last_Posted"] = datetime.now().strftime("%Y-%m-%d/%H:%M")

			# Write updated quote metadata back to file
			f.seek(0)
			json.dump(quotes, f, indent=2)
			f.truncate()
except Exception as e:
	if args.dryrun:
		print(f"Quote file check: Fail\n{QUOTE_FILE} ({e})")
		raise SystemExit(1)
	raise
