#!/usr/bin/env python3
"""
Generate a modern, futuristic GitHub contributions SVG line chart (no fill).
Uses GitHub GraphQL API and writes a static SVG file to disk.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
import os
import sys
import urllib.request

GITHUB_API = "https://api.github.com/graphql"

BG = "#1e1e1e"
STROKE = "#E65729"
TEXT = "#ffffff"


def _github_token() -> str:
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_PAT")
    if not token:
        raise RuntimeError("Missing GitHub token. Set GITHUB_TOKEN or GH_PAT.")
    return token


def _request_graphql(query: str, variables: dict) -> dict:
    payload = json.dumps({"query": query, "variables": variables}).encode("utf-8")
    req = urllib.request.Request(GITHUB_API, data=payload, method="POST")
    req.add_header("Authorization", f"bearer {_github_token()}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=20) as res:
        body = res.read().decode("utf-8")
        if res.status != 200:
            raise RuntimeError(f"GitHub API error: {res.status} {body}")
        return json.loads(body)


def fetch_contributions(username: str, year: int) -> list[dict]:
    start = f"{year}-01-01T00:00:00Z"
    end = f"{year}-12-31T23:59:59Z"
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    variables = {"login": username, "from": start, "to": end}
    payload = _request_graphql(query, variables)
    if "errors" in payload:
        raise RuntimeError(json.dumps(payload["errors"]))

    weeks = (
        payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    )
    days = []
    for w in weeks:
        for d in w["contributionDays"]:
            days.append({"date": d["date"], "count": d["contributionCount"]})
    days.sort(key=lambda x: x["date"])
    return days


def _month_labels(days: list[dict]) -> list[tuple[int, str]]:
    labels = []
    for i, d in enumerate(days):
        date_obj = dt.date.fromisoformat(d["date"])
        if date_obj.day == 1 and date_obj.month in (1, 4, 7, 10):
            labels.append((i, date_obj.strftime("%b")))
    return labels


def build_svg(
    days: list[dict],
    width: int = 1200,
    height: int = 360,
    padding: int = 52,
    bg: str = BG,
    stroke: str = STROKE,
    text: str = TEXT,
) -> str:
    if not days:
        return (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
            f'<rect width="100%" height="100%" fill="{bg}"/>'
            "</svg>"
        )

    inner_w = width - padding * 2
    inner_h = height - padding * 2
    counts = [d["count"] for d in days]
    max_c = max(counts) if counts else 1
    total = sum(counts)

    n = len(days)
    xs = [padding + (i / (n - 1)) * inner_w for i in range(n)]

    def y_for_count(c: int) -> float:
        if max_c > 20:
            norm = math.log1p(c) / math.log1p(max_c)
        else:
            norm = c / max_c if max_c else 0
        return padding + (1 - norm) * inner_h

    ys = [y_for_count(c) for c in counts]
    path = "".join(
        ("M" if i == 0 else "L") + f"{x:.2f},{y:.2f}"
        for i, (x, y) in enumerate(zip(xs, ys))
    )

    labels = _month_labels(days)

    grid_lines = 5
    grid = []
    for i in range(grid_lines + 1):
        y = padding + (i / grid_lines) * inner_h
        grid.append(
            f'<line x1="{padding}" y1="{y:.2f}" x2="{width - padding}" y2="{y:.2f}" '
            f'stroke="{text}" stroke-opacity="0.08" stroke-width="1" />'
        )

    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="GitHub contributions line chart">',
        f'<rect width="100%" height="100%" fill="{bg}" rx="14" ry="14"/>',
        '<defs>',
        '<filter id="glow" x="-50%" y="-50%" width="200%" height="200%">',
        '<feGaussianBlur stdDeviation="3" result="coloredBlur"/>',
        '<feMerge>',
        '<feMergeNode in="coloredBlur"/>',
        '<feMergeNode in="SourceGraphic"/>',
        "</feMerge>",
        "</filter>",
        "</defs>",
        f'<text x="{padding}" y="{padding - 16}" fill="{text}" '
        'font-family="Space Grotesk, Orbitron, Rajdhani, Arial, sans-serif" '
        'font-size="20" font-weight="700">GitHub Contributions</text>',
        f'<text x="{padding}" y="{padding + 6}" fill="{text}" '
        'font-family="Space Grotesk, Orbitron, Rajdhani, Arial, sans-serif" '
        f'font-size="12" opacity="0.8">Year {days[0]["date"][:4]} • Total {total}</text>',
        *grid,
        f'<path d="{path}" fill="none" stroke="{stroke}" stroke-width="2.6" '
        'stroke-linejoin="round" stroke-linecap="round" filter="url(#glow)"/>',
        f'<path d="{path}" fill="none" stroke="{stroke}" stroke-width="1.4" '
        'stroke-linejoin="round" stroke-linecap="round"/>',
    ]

    for idx, label in labels:
        x = xs[idx]
        svg.append(
            f'<text x="{x:.2f}" y="{height - padding + 24}" fill="{text}" '
            'font-family="Space Grotesk, Orbitron, Rajdhani, Arial, sans-serif" '
            'font-size="11" text-anchor="middle" opacity="0.9">'
            f"{label}</text>"
        )

    svg.append(
        f'<text x="{width - padding}" y="{padding - 10}" fill="{text}" '
        'font-family="Space Grotesk, Orbitron, Rajdhani, Arial, sans-serif" '
        f'font-size="11" text-anchor="end" opacity="0.8">max: {max_c}</text>'
    )
    svg.append("</svg>")
    return "\n".join(svg)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", required=True, help="GitHub username")
    parser.add_argument("--year", type=int, default=dt.datetime.utcnow().year)
    parser.add_argument("--out", default="assets/contributions.svg")
    args = parser.parse_args()

    days = fetch_contributions(args.user, args.year)
    svg = build_svg(days)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(svg)

    return 0


if __name__ == "__main__":
    sys.exit(main())
