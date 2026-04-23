import os
import re
import time
import requests
from datetime import datetime, timedelta, timezone
from dateutil.parser import parse as parse_date


class GithubFetcher:

    BASE = "https://api.github.com"

    def __init__(self, org):
        self.org = org
        self.session = requests.Session()
        headers = {"Accept": "application/vnd.github+json"}
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"token {token}"
        else:
            print("Warning: GITHUB_TOKEN not set — using unauthenticated API (60 req/hour limit)")
        self.session.headers.update(headers)

    def get(self, path, params=None):
        url = f"{self.BASE}{path}"
        r = self.session.get(url, params=params)
        remaining = int(r.headers.get("X-RateLimit-Remaining", 1))
        if remaining < 5:
            reset = int(r.headers.get("X-RateLimit-Reset", time.time() + 60))
            sleep = max(reset - time.time(), 0) + 2
            print(f"Rate limit low. Sleeping {sleep:.0f}s")
            time.sleep(sleep)
        r.raise_for_status()
        return r.json()

    def paginate(self, path, params=None, max_pages=10):
        params = params or {}
        results = []
        for page in range(1, max_pages + 1):
            params["page"] = page
            params["per_page"] = 100
            data = self.get(path, params)
            if not data:
                break
            results.extend(data)
            if len(data) < 100:
                break
        return results

    def collect(self, founding_team_handles=None, sample_size=None):
        now = datetime.now(timezone.utc)
        cutoff_90d = now - timedelta(days=90)
        cutoff_30d = now - timedelta(days=30)

        metrics = {}

        # --- all repos ---
        print(f"Fetching repos for {self.org}...")
        all_repos = self.paginate(f"/orgs/{self.org}/repos",
                                  {"sort": "pushed", "direction": "desc"})
        print(f"  {len(all_repos)} repos found")

        # delivery continuity
        if all_repos:
            latest_push = parse_date(all_repos[0]["pushed_at"])
            metrics["most_recent_push_days_ago"] = (now - latest_push).days

        # newest non-fork repo
        non_forks = [r for r in all_repos if not r["fork"]]
        sorted_by_created = sorted(non_forks,
                                   key=lambda r: r["created_at"],
                                   reverse=True)
        if sorted_by_created:
            newest = parse_date(sorted_by_created[0]["created_at"])
            metrics["newest_non_fork_days_old"] = (now - newest).days

        # active repos in last 90 days
        active_repos = [
            r for r in all_repos
            if parse_date(r["pushed_at"]) > cutoff_90d
        ]

        # AI-adjacent active repos
        ai_pattern = r"ai|llm|agent|mcp|inference|embedding"
        active_ai = [
            r for r in active_repos
            if re.search(ai_pattern,
                        (r.get("description") or "") + " " + r["name"],
                        re.IGNORECASE)
        ]
        metrics["active_ai_repos"] = len(active_ai)

        # MCP repos specifically
        active_mcp = [r for r in active_repos
                      if re.search(r"mcp", r["name"] + " " +
                                   (r.get("description") or ""),
                                   re.IGNORECASE)]
        metrics["active_mcp_repos"] = len(active_mcp)

        # --- contributors and authors ---
        if sample_size is None:
            sample_size = 10 if len(all_repos) < 50 else 5
        all_non_forks = [r["name"] for r in all_repos if not r["fork"]]
        sample_repos = all_non_forks[:sample_size]
        print(f"Sampling {len(sample_repos)} repos (sample_size={sample_size}, non-forks={len(all_non_forks)})")

        unique_authors = set()
        since_90d = cutoff_90d.strftime("%Y-%m-%dT%H:%M:%SZ")
        print(f"Fetching commits for: {', '.join(sample_repos)}")
        for repo in sample_repos:
            try:
                print(f"  → {repo}...")
                commits = self.paginate(
                    f"/repos/{self.org}/{repo}/commits",
                    {"since": since_90d},
                )
                for commit in commits:
                    author = (commit.get("author") or {}).get("login")
                    if author:
                        unique_authors.add(author)
            except Exception:
                continue

        metrics["unique_active_authors_90d"] = len(unique_authors)

        # founding team activity
        if founding_team_handles:
            founding_set = {h.lower() for h in founding_team_handles}
            active_founders = {a for a in unique_authors if a.lower() in founding_set}
            metrics["founding_team_active_committers"] = len(active_founders)
            if active_founders:
                print(f"  Founding team active: {', '.join(active_founders)}")
            else:
                print(f"  No founding team members found in commits")

        # external contributors — check if contributors exist
        # outside the org member list (approximation)
        metrics["has_external_contributors"] = len(unique_authors) > 5

        # --- PR velocity ---
        print("Fetching PR velocity...")
        merged_count = 0
        for repo in sample_repos[:3]:
            try:
                prs = self.get(
                    f"/repos/{self.org}/{repo}/pulls",
                    {"state": "closed", "per_page": 50, "sort": "updated"}
                )
                for pr in prs:
                    if pr.get("merged_at"):
                        merged_at = parse_date(pr["merged_at"])
                        if merged_at > cutoff_30d:
                            merged_count += 1
            except Exception:
                continue

        metrics["merged_prs_30d"] = merged_count

        return metrics
