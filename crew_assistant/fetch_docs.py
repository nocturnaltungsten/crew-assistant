# fetch_docs.py
# Pulls documentation from GitHub repos listed in TECH_STACK.md

import os
import re
import requests
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).parent
TECH_FILE = ROOT / "TECH_STACK.md"
DOCS_DIR = ROOT / "docs"
GITHUB_API = "https://api.github.com/repos"

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
}


def extract_github_links(md_file):
    text = md_file.read_text()
    return re.findall(r"https://github.com/[^\s)]+", text)


def repo_to_slug(url):
    parts = urlparse(url).path.strip("/").split("/")
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return None


def fetch_and_save_file(repo, path, save_to):
    raw_url = f"https://raw.githubusercontent.com/{repo}/main/{path}"
    r = requests.get(raw_url)
    if r.status_code == 200:
        save_to.write_text(r.text)
        print(f"✅ {repo} -> {path}")
    else:
        print(f"❌ Failed: {repo}/{path} ({r.status_code})")


def fetch_docs(repo_slug):
    repo_dir = DOCS_DIR / repo_slug.replace("/", "--")
    repo_dir.mkdir(parents=True, exist_ok=True)

    # Try README.md
    fetch_and_save_file(repo_slug, "README.md", repo_dir / "README.md")

    # Try common docs folders
    for folder in ["docs", "documentation", "wiki"]:
        api_url = f"{GITHUB_API}/{repo_slug}/contents/{folder}"
        r = requests.get(api_url, headers=HEADERS)
        if r.status_code != 200:
            continue

        files = r.json()
        for f in files:
            if f['type'] == 'file' and f['name'].endswith(('.md', '.txt')):
                fetch_and_save_file(
                    repo_slug,
                    f"{folder}/{f['name']}",
                    repo_dir / f['name']
                )


def main():
    print("\n📥 Starting doc fetcher from TECH_STACK.md...\n")
    DOCS_DIR.mkdir(exist_ok=True)
    links = extract_github_links(TECH_FILE)
    slugs = list(filter(None, map(repo_to_slug, links)))

    for slug in slugs:
        fetch_docs(slug)

    print("\n📚 Doc fetch complete.")


if __name__ == "__main__":
    main()
