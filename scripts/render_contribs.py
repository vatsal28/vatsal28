#!/usr/bin/env python3
"""Render the current calendar year's GitHub contribution matrix as SVG.

Fetches the contribution calendar via GitHub GraphQL (token from
GITHUB_TOKEN or GH_TOKEN) and writes light/dark SVGs to assets/.
"""
import datetime
import json
import os
import urllib.request

USER = "vatsal28"
YEAR = datetime.date.today().year

PALETTES = {
    "light": {
        "NONE": "#ebedf0", "FIRST_QUARTILE": "#9be9a8",
        "SECOND_QUARTILE": "#40c463", "THIRD_QUARTILE": "#30a14e",
        "FOURTH_QUARTILE": "#216e39", "text": "#57606a",
    },
    "dark": {
        "NONE": "#161b22", "FIRST_QUARTILE": "#0e4429",
        "SECOND_QUARTILE": "#006d32", "THIRD_QUARTILE": "#26a641",
        "FOURTH_QUARTILE": "#39d353", "text": "#8b949e",
    },
}

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date weekday contributionLevel } }
      }
    }
  }
}
"""


def fetch_calendar():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise SystemExit("GITHUB_TOKEN/GH_TOKEN not set")
    body = json.dumps({
        "query": QUERY,
        "variables": {
            "login": USER,
            "from": f"{YEAR}-01-01T00:00:00Z",
            "to": f"{YEAR}-12-31T23:59:59Z",
        },
    }).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=body,
        headers={"Authorization": f"bearer {token}",
                 "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    if "errors" in data:
        raise SystemExit(f"GraphQL errors: {data['errors']}")
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def render(cal, palette):
    cell, pitch = 11, 14
    top, left = 46, 8
    weeks = cal["weeks"]
    width = left + len(weeks) * pitch + 8
    height = top + 7 * pitch + 6
    p = PALETTES[palette]
    font = "font-family='-apple-system,BlinkMacSystemFont,Segoe UI,Helvetica,Arial,sans-serif'"

    out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' "
           f"height='{height}' viewBox='0 0 {width} {height}'>"]
    out.append(f"<text x='{left}' y='16' font-size='13' {font} "
               f"fill='{p['text']}'>{cal['totalContributions']} contributions in {YEAR}</text>")

    seen_months = set()
    for wi, week in enumerate(weeks):
        days = week["contributionDays"]
        first = datetime.date.fromisoformat(days[0]["date"])
        if first.month not in seen_months and first.day <= 14:
            seen_months.add(first.month)
            out.append(f"<text x='{left + wi * pitch}' y='38' font-size='11' "
                       f"{font} fill='{p['text']}'>{first.strftime('%b')}</text>")
        for d in days:
            x = left + wi * pitch
            y = top + d["weekday"] * pitch
            out.append(f"<rect x='{x}' y='{y}' width='{cell}' height='{cell}' "
                       f"rx='2' fill='{p[d['contributionLevel']]}'/>")
    out.append("</svg>")
    return "".join(out)


def main():
    cal = fetch_calendar()
    os.makedirs("assets", exist_ok=True)
    for palette, name in (("light", "contribs.svg"), ("dark", "contribs-dark.svg")):
        path = os.path.join("assets", name)
        with open(path, "w") as f:
            f.write(render(cal, palette))
        print(f"wrote {path}")
    print(f"total: {cal['totalContributions']}")


if __name__ == "__main__":
    main()
