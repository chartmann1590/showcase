#!/usr/bin/env python3
"""
Generate catalog.json and sitemap.xml from the GitHub API.
Run locally or via GitHub Actions (uses GITHUB_TOKEN env var automatically).
"""

import os
import json
import requests
from datetime import datetime, timezone

GITHUB_USERNAME = "chartmann1590"
SHOWCASE_URL = "https://chartmann1590.github.io/showcase"
BUYMEACOFFEE_URL = "https://buymeacoffee.com/charleshartmann"

# Game detection patterns
GAME_NAME_SIGNALS = ["shooter", "simulator", "chess", "fish-tank", "spaceshooter", "space-shooter", "eldoria"]
GAME_TOPIC_SIGNALS = ["game", "android-game", "game-development", "rpg", "arcade", "puzzle"]
GAME_DESC_SIGNALS = [
    "turn-based rpg", "boss battles", "virtual pet game", "space shooter game",
    "fun business simulator", "jury duty simulator", "android game",
    "feature-rich space shooter",
]

# IoT/hardware patterns (name + description search)
IOT_SIGNALS = ["raspberry", "rpi", "esp32", "wearable", "rokid", "lifecapture"]

# AI-specific patterns for non-Python/non-mobile repos
WEB_AI_SIGNALS = ["ollama", "llm", "whisper", "gemma", "langchain", "openai"]


def get_headers():
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github.v3+json", "User-Agent": "showcase-bot"}
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def fetch_profile():
    r = requests.get(
        f"https://api.github.com/users/{GITHUB_USERNAME}",
        headers=get_headers(),
        timeout=15,
    )
    r.raise_for_status()
    return r.json()


def fetch_all_repos():
    repos, page = [], 1
    while True:
        r = requests.get(
            f"https://api.github.com/users/{GITHUB_USERNAME}/repos",
            params={"per_page": 100, "page": page, "type": "owner", "sort": "pushed"},
            headers=get_headers(),
            timeout=15,
        )
        r.raise_for_status()
        batch = r.json()
        if not batch:
            break
        repos.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return repos


def detect_category(repo):
    name = repo.get("name", "").lower()
    desc = (repo.get("description") or "").lower()
    lang = (repo.get("language") or "").lower()
    topics = [t.lower() for t in (repo.get("topics") or [])]
    combined = f"{name} {desc} {' '.join(topics)}"

    # Games: check name signals first (strongest), then description, then topics
    if any(sig in name for sig in GAME_NAME_SIGNALS):
        return "game"
    if any(sig in topics for sig in GAME_TOPIC_SIGNALS):
        return "game"
    if any(sig in desc for sig in GAME_DESC_SIGNALS):
        return "game"
    # pixel-fish-tank special case
    if "pixel" in name and "fish" in combined:
        return "game"

    # Android apps (Kotlin or Java = mobile platform)
    if lang in ("kotlin", "java"):
        return "android"

    # IoT / Hardware (check before Python/web)
    if any(sig in combined for sig in IOT_SIGNALS):
        return "iot"

    # Python tools
    if lang == "python":
        return "python"

    # Web apps with strong AI/LLM focus
    if lang in ("javascript", "typescript", "html", "css"):
        if any(sig in combined for sig in WEB_AI_SIGNALS):
            return "ai"
        return "web"

    # Catch-all AI for other languages
    if any(sig in combined for sig in WEB_AI_SIGNALS):
        return "ai"

    # C / other systems languages with hardware context
    if lang in ("c", "c++", "go"):
        return "iot"

    return "other"


def format_date(date_str):
    return date_str[:10] if date_str else ""


def main():
    print("Fetching GitHub profile...")
    profile = fetch_profile()

    print("Fetching repositories...")
    all_repos = fetch_all_repos()

    # Keep only original (non-fork), public, non-archived repos
    repos = [
        r for r in all_repos
        if not r.get("fork") and not r.get("private") and not r.get("archived")
    ]
    print(f"  {len(all_repos)} total -> {len(repos)} original public repos")

    repos_data = []
    for r in repos:
        repos_data.append({
            "name": r["name"],
            "description": r.get("description") or "",
            "url": r["html_url"],
            "homepage": r.get("homepage") or "",
            "language": r.get("language") or "",
            "stars": r.get("stargazers_count") or 0,
            "forks": r.get("forks_count") or 0,
            "topics": r.get("topics") or [],
            "category": detect_category(r),
            "pushed_at": format_date(r.get("pushed_at")),
            "created_at": format_date(r.get("created_at")),
        })

    # Sort: stars descending, then name ascending
    repos_data.sort(key=lambda x: (-x["stars"], x["name"].lower()))

    # Build category counts
    by_category = {}
    for repo in repos_data:
        cat = repo["category"]
        by_category[cat] = by_category.get(cat, 0) + 1

    total_stars = sum(r["stars"] for r in repos_data)

    catalog = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "profile": {
            "login": profile.get("login", GITHUB_USERNAME),
            "name": profile.get("name") or "Charles Hartmann",
            "bio": profile.get("bio") or "",
            "avatar_url": profile.get("avatar_url") or f"https://github.com/{GITHUB_USERNAME}.png",
            "html_url": profile.get("html_url") or f"https://github.com/{GITHUB_USERNAME}",
            "public_repos": profile.get("public_repos") or 0,
            "followers": profile.get("followers") or 0,
        },
        "stats": {
            "total": len(repos_data),
            "total_stars": total_stars,
            "by_category": by_category,
        },
        "showcase_url": SHOWCASE_URL,
        "buymeacoffee_url": BUYMEACOFFEE_URL,
        "repos": repos_data,
    }

    with open("catalog.json", "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)
    print("catalog.json written")

    # Generate sitemap.xml
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        f"  <url><loc>{SHOWCASE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>",
    ]
    for repo in repos_data:
        slug = repo["name"].lower().replace("_", "-")
        lines.append(
            f"  <url><loc>{SHOWCASE_URL}/#app-{slug}</loc><changefreq>weekly</changefreq><priority>0.6</priority></url>"
        )
    lines.append("</urlset>")

    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("sitemap.xml written")

    # Summary
    print(f"\nStats: {len(repos_data)} repos | {total_stars} total stars")
    for cat, count in sorted(by_category.items(), key=lambda x: -x[1]):
        print(f"   {cat:12s}: {count}")


if __name__ == "__main__":
    main()
