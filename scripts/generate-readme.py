#!/usr/bin/env python3
"""
Generate README.md from catalog.json.
Run after generate-catalog.py.
"""

import json
from datetime import date

BUYMEACOFFEE_URL = "https://buymeacoffee.com/charleshartmann"
SHOWCASE_URL = "https://chartmann1590.github.io/showcase"
GITHUB_PROFILE  = "https://github.com/chartmann1590"
GOOGLE_PLAY_URL = "https://play.google.com/store/apps/developer?id=Hartmann+Studios"


CATEGORY_META = {
    "android": ("📱", "Android Apps"),
    "web":     ("🌐", "Web Applications"),
    "ai":      ("🤖", "AI & LLM Tools"),
    "python":  ("🐍", "Python Tools"),
    "game":    ("🎮", "Games"),
    "iot":     ("🔧", "IoT & Hardware"),
    "other":   ("⚙️",  "Other Projects"),
}

CATEGORY_ORDER = ["android", "web", "ai", "python", "game", "iot", "other"]


def repo_table_row(r):
    name_link = f"[{r['name']}]({r['url']})"
    desc = r.get("description") or "—"
    stars = f"⭐ {r['stars']}" if r["stars"] else ""
    lang = r.get("language") or ""
    homepage = f" · [Demo]({r['homepage']})" if r.get("homepage") else ""
    return f"| {name_link} | {desc}{homepage} | {lang} | {stars} |"


def main():
    with open("catalog.json", encoding="utf-8") as f:
        catalog = json.load(f)

    profile = catalog["profile"]
    stats = catalog["stats"]
    repos = catalog["repos"]
    updated = catalog.get("updated", str(date.today()))

    # Featured: top 6 by stars (min 1 star)
    featured = [r for r in repos if r["stars"] >= 1][:6]

    total = stats["total"]
    total_stars = stats.get("total_stars", 0)
    by_cat = stats.get("by_category", {})

    # ---------- Build README content ----------
    lines = []

    # Header
    lines += [
        '<div align="center">',
        "",
        f'<img src="https://github.com/chartmann1590.png" alt="Charles Hartmann" width="100" height="100" style="border-radius:50%;"/>',
        "",
        "# ✨ Charles Hartmann's App Portfolio",
        "",
        "**Android apps · AI tools · Web platforms · Python scripts — all open source**",
        "",
        f'[![Apps](https://img.shields.io/badge/Apps-{total}-4f6fff?style=for-the-badge&logo=github&logoColor=white)]({SHOWCASE_URL})',
        f'[![Stars](https://img.shields.io/badge/Total_Stars-{total_stars}-gold?style=for-the-badge&logo=github&logoColor=white)]({GITHUB_PROFILE})',
        f'[![Buy Me a Coffee](https://img.shields.io/badge/Buy_Me_a_Coffee-☕-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)]({BUYMEACOFFEE_URL})',
        f'[![Google Play](https://img.shields.io/badge/Google_Play-Hartmann_Studios-01875f?style=for-the-badge&logo=google-play&logoColor=white)]({GOOGLE_PLAY_URL})',
        "",
        f'### 🌐 [View the Full Interactive Showcase →]({SHOWCASE_URL})',
        "",
        "> Hi! I'm Charles — a versatile programmer specializing in Android, AI, and automation.",
        "> If any of my projects helped you, consider supporting my work!",
        "",
        f"**☕ [{BUYMEACOFFEE_URL}]({BUYMEACOFFEE_URL})**",
        "",
        "</div>",
        "",
        "---",
        "",
    ]

    # Featured projects
    if featured:
        lines += [
            "## ⭐ Featured Projects",
            "",
            "| Project | Description | Stars |",
            "|---------|-------------|-------|",
        ]
        for r in featured:
            desc = r.get("description") or "—"
            homepage_link = f" · [Live]({r['homepage']})" if r.get("homepage") else ""
            lines.append(f"| [{r['name']}]({r['url']}) | {desc}{homepage_link} | ⭐ {r['stars']} |")
        lines += ["", "---", ""]

    # Categories
    for cat in CATEGORY_ORDER:
        cat_repos = [r for r in repos if r["category"] == cat]
        if not cat_repos:
            continue
        icon, label = CATEGORY_META.get(cat, ("📦", cat.title()))
        count = len(cat_repos)
        lines += [
            f"## {icon} {label} ({count})",
            "",
            "| App | Description | Language | Stars |",
            "|-----|-------------|----------|-------|",
        ]
        for r in cat_repos:
            lines.append(repo_table_row(r))
        lines += [""]

    # Support section
    lines += [
        "---",
        "",
        '<div align="center">',
        "",
        "## ☕ Support My Work",
        "",
        "If you find my projects useful, consider buying me a coffee!",
        "",
        f'<a href="{BUYMEACOFFEE_URL}" target="_blank">',
        f'  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="50">',
        "</a>",
        "&nbsp;&nbsp;",
        f'<a href="{GOOGLE_PLAY_URL}" target="_blank">',
        f'  <img src="https://upload.wikimedia.org/wikipedia/commons/7/78/Google_Play_Store_badge_EN.svg" alt="Get it on Google Play" height="50">',
        "</a>",
        "",
        f'*🤖 This README is auto-updated daily via [GitHub Actions](https://github.com/chartmann1590/showcase/actions) · Last updated: {updated}*',
        "",
        "</div>",
    ]

    readme_content = "\n".join(lines) + "\n"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"README.md written ({len(repos)} repos, {len(featured)} featured)")


if __name__ == "__main__":
    main()
