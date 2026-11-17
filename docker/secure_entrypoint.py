#!/usr/bin/env python3
"""Load application secrets and seed a writable Telethon session at runtime."""

import argparse
import os
import shutil
import sys
from pathlib import Path

from dotenv import dotenv_values


def load_environment(secret_path: Path) -> None:
    if not secret_path.is_file():
        raise FileNotFoundError(f"Application environment secret not found: {secret_path}")

    for key, value in dotenv_values(secret_path).items():
        if key and value is not None:
            os.environ.setdefault(key, value)


def seed_session(secret_path: Path, target_path: Path) -> None:
    if not secret_path.is_file():
        raise FileNotFoundError(f"Telegram session secret not found: {secret_path}")

    target_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(target_path.parent, 0o700)
    if not target_path.exists() or target_path.stat().st_size == 0:
        temporary = target_path.with_suffix(target_path.suffix + ".tmp")
        shutil.copyfile(secret_path, temporary)
        os.chmod(temporary, 0o600)
        os.replace(temporary, target_path)
    os.chmod(target_path, 0o600)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-secret", required=True, type=Path)
    parser.add_argument("--session-secret", required=True, type=Path)
    parser.add_argument("--session-target", required=True, type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command and args.command[0] == "--":
        args.command = args.command[1:]
    if not args.command:
        parser.error("command after -- is required")
    return args


def main() -> None:
    args = parse_args()
    load_environment(args.env_secret)
    seed_session(args.session_secret, args.session_target)
    os.execvp(args.command[0], args.command)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"secure entrypoint failed: {exc}", file=sys.stderr)
        raise
