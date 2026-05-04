#!/usr/bin/env python3
import argparse
import subprocess
import sys


COMMANDS = {
    "inference": ["inference.py"],
    "tag-language": ["scripts/tag_language.py"],
    "preprocess": ["scripts/preprocess_text.py"],
    "sentiment": ["scripts/run_sentiment.py"],
    "topics": ["scripts/run_topics.py"],
    "validate": ["scripts/validate_data_contract.py"],
}


def main() -> int:
    parser = argparse.ArgumentParser(description="MBG pipeline CLI dispatcher")
    parser.add_argument("stage", choices=COMMANDS.keys(), help="Pipeline stage to run")
    parser.add_argument("extra_args", nargs=argparse.REMAINDER, help="Extra args passed to the stage script")
    args = parser.parse_args()

    # FIX: replace duplicate runner with thin dispatcher to canonical scripts.
    cmd = [sys.executable] + COMMANDS[args.stage] + args.extra_args
    return subprocess.run(cmd).returncode


if __name__ == "__main__":
    raise SystemExit(main())

