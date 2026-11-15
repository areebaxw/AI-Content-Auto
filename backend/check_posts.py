#!/usr/bin/env python3
"""Check a posts JSON file against the platform counts and length limits.

Usage: python scripts/check_posts.py posts.json
Standard library only. Exits 0 when everything fits, 1 otherwise.
"""
from __future__ import annotations

import json
import sys

RULES = {
    "twitter": {"count": 5, "max_chars": 280},
    "linkedin": {"count": 2, "max_chars": 1300},
    "telegram": {"count": 3, "max_chars": 500},
    "instagram": {"count": 1, "max_chars": 2200},
}


def check(posts: dict) -> list[str]:
    problems: list[str] = []
    for platform, rule in RULES.items():
        items = posts.get(platform)
        if not isinstance(items, list):
            problems.append(f"{platform}: missing or not a list")
            continue
        if len(items) != rule["count"]:
            problems.append(f"{platform}: expected {rule['count']} items, found {len(items)}")
        for index, item in enumerate(items, start=1):
            if not isinstance(item, str) or not item.strip():
                problems.append(f"{platform} #{index}: empty or not text")
            elif len(item) > rule["max_chars"]:
                problems.append(f"{platform} #{index}: {len(item)} characters, limit is {rule['max_chars']}")
    email = posts.get("email")
    if not isinstance(email, dict) or not email.get("subject") or not email.get("body"):
        problems.append("email: needs an object with a subject and a body")
    return problems


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    with open(sys.argv[1], encoding="utf-8") as handle:
        posts = json.load(handle)
    problems = check(posts)
    for platform, rule in RULES.items():
        items = posts.get(platform) if isinstance(posts.get(platform), list) else []
        longest = max((len(item) for item in items if isinstance(item, str)), default=0)
        print(f"{platform:10} {len(items)}/{rule['count']} items, longest {longest}/{rule['max_chars']} chars")
    if problems:
        print("\nProblems:")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print("\nAll posts fit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
