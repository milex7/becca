#!/usr/bin/env python3
"""Generate a password containing ASCII letters and digits."""

from __future__ import annotations

import argparse
import secrets
import string


DEFAULT_LENGTH = 12
CHARACTERS = string.ascii_letters + string.digits


def generate_password(length: int) -> str:
    """Return a cryptographically secure password with the requested length."""
    if length < 1:
        raise ValueError("密码长度必须大于 0")
    return "".join(secrets.choice(CHARACTERS) for _ in range(length))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="随机生成由数字及大小写英文字母组成的密码。"
    )
    parser.add_argument(
        "-l",
        "--length",
        type=int,
        default=DEFAULT_LENGTH,
        help=f"密码长度（默认：{DEFAULT_LENGTH}）",
    )
    args = parser.parse_args()
    if args.length < 1:
        parser.error("--length 必须大于 0")
    return args


def main() -> None:
    args = parse_args()
    print(generate_password(args.length))


if __name__ == "__main__":
    main()
