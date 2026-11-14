"""Commit log: the latest pushes as a neo-brutalist card, newest on top with a
sticker and an emerald block.

Commits come from GraphQL: the owner's most recently pushed public repositories,
each repository's default-branch history filtered to commits the owner authored.
Only public repositories are read, so a token that can see private work never
leaks a private commit message onto the profile. Nothing here is invented: with
no token or no commits, the existing log is left untouched.

    GITHUB_TOKEN=... python scripts/build_log.py
    PROFILE_LOG_FIXTURE=commits.json python scripts/build_log.py   # offline
"""
import datetime as dt
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mc  # noqa: E402
from brut import (CARD_H, HALF, INK, MUTED, PINK, RED, WHITE, YELLOW, box, card, mono, sticker, svg,  # noqa: E402
                  tab, text)
from theme import ASSETS  # noqa: E402

LOGIN = os.environ.get("PROFILE_LOGIN", "ZainulArkaanAlinsi")
TZ = dt.timezone(dt.timedelta(hours=7))  # WIB
SKIP = ("chore: refresh profile assets",)   # the bot's own commits on this repo

QUERY = """query($login:String!,$id:ID!){ user(login:$login){
  repositories(first:8, privacy:PUBLIC, ownerAffiliations:[OWNER], orderBy:{field:PUSHED_AT,direction:DESC}){
    nodes{ name isFork primaryLanguage{ name color }
      defaultBranchRef{ target{ ... on Commit{ history(first:8, author:{id:$id}){
        nodes{ oid messageHeadline committedDate additions deletions } } } } } } } } }"""


def gql(query, **variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
                 "Content-Type": "application/json", "User-Agent": "profile-log"})
    with urllib.request.urlopen(req, timeout=30) as r:
        payload = json.load(r)
    if payload.get("errors"):
        raise RuntimeError(payload["errors"])
    return payload["data"]


def fetch():
    fixture = os.environ.get("PROFILE_LOG_FIXTURE")
    if fixture:
        with open(fixture, encoding="utf-8") as f:
            return json.load(f)
    uid = gql("query($login:String!){ user(login:$login){ id } }", login=LOGIN)["user"]["id"]
    repos = gql(QUERY, login=LOGIN, id=uid)["user"]["repositories"]["nodes"]
    return flatten(repos)


def flatten(repos):
    """Repository nodes -> one list of commits, newest first."""
    out = []
    for r in repos:
        ref = r.get("defaultBranchRef") or {}
        hist = ((ref.get("target") or {}).get("history") or {}).get("nodes") or []
        lang = r.get("primaryLanguage") or {}
        for c in hist:
            if c["messageHeadline"].strip().lower().startswith(SKIP):
                continue
            out.append({"repo": r["name"], "message": c["messageHeadline"].strip(),
                        "language": lang.get("name") or "", "color": lang.get("color") or "",
                        "additions": c.get("additions") or 0, "deletions": c.get("deletions") or 0,
                        "oid": c["oid"][:7], "date": c["committedDate"]})
    out.sort(key=lambda c: c["date"], reverse=True)
    return out


def local(iso):
    return dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(TZ)


def trim(s, n):
    s = " ".join(s.split())
    return s if len(s) <= n else s[:max(1, n - 1)].rstrip() + "…"


TYPES = {"feat": ("FEAT", "#A3E635"), "fix": ("FIX", "#FF5A5F"), "style": ("STYLE", "#FF7AB6"),
         "docs": ("DOCS", "#5AA9FF"), "refactor": ("REFAC", "#B794F6"), "chore": ("CHORE", "#FFD23F"),
         "test": ("TEST", "#5AA9FF"), "perf": ("PERF", "#FF9F43"), "init": ("INIT", "#FFD23F")}


def kind(message):
    """Conventional-commit prefix -> (tag, colour); anything else is a plain commit."""
    head = message.split(":", 1)[0].split("(", 1)[0].lower().strip() if ":" in message else ""
    return TYPES.get(head, ("COMMIT", "#FFFFFF"))


def body_of(message):
    """The message without its conventional prefix, since the tag shows it."""
    head = message.split(":", 1)
    return head[1].strip() if len(head) == 2 and head[0].split("(", 1)[0].lower().strip() in TYPES else message


CSS = ("@keyframes slide{from{opacity:0;transform:translateX(-24px)}to{opacity:1;transform:none}}"
       ".ln{animation:slide .45s ease-out both}")
LINES = 6


def render(commits, stamp):
    w, h = HALF, CARD_H
    out = [card(w, h)]
    out.append(tab(26, 24, "COMMIT LOG")[0])
    out.append(f'<circle class="pulse" cx="{w - 132}" cy="46" r="7" fill="{RED}" stroke="{INK}" stroke-width="2"/>')
    out.append(mono(w - 118, 51, "LIVE", 15, INK, weight=900))
    out.append(mono(w / 2, h - 22, f"synced {stamp} · refreshed on every push", 12, MUTED, "middle", 600))
    y, row = 86, 70
    for i, c in enumerate(commits[:LINES]):
        tag, col = kind(c["message"])
        newest = i == 0
        g = [box(26, y, w - 26 * 2 - 6, row - 12, YELLOW if newest else WHITE, sh=4)]
        g.append(box(38, y + 12, len(tag) * 9 + 16, 22, col, sh=0, bw=2))
        g.append(mono(46, y + 28, tag, 12, INK, weight=900))
        tx = 38 + len(tag) * 9 + 26
        g.append(text(tx, y + 29, trim(body_of(c["message"]), int((w - tx - 60) / 8.2)), 15, INK, weight=800))
        meta = (f"{c['repo']} · {c['oid']} · +{c['additions']:,} −{c['deletions']:,} · "
                f"{local(c['date']).strftime('%d %b %H:%M')}")
        g.append(mono(38, y + 50, trim(meta, 64), 11.5, MUTED, weight=600))
        out.append(f'<g class="ln" style="animation-delay:{.3 + i * .15:.2f}s">{"".join(g)}</g>')
        y += row
    if commits:
        out.append(sticker(w - 70, 88, "NEW!", PINK, 8, 16, cls="wob"))
        out.append(f'<g class="bob">{mc.image(mc.png_uri(mc.icon("emerald_block", 96)), 214, 28, 38, 38)}</g>')
    else:
        out.append(text(w / 2, h / 2, "no public commits yet", 18, MUTED, "middle", 700))
    newest = commits[0]["message"] if commits else "no commits yet"
    return svg(w, h, "".join(out), css=CSS,
               label=f"Commit log: latest commit '{newest}', plus the {min(len(commits), LINES)} most recent commits")


def main():
    if not os.environ.get("PROFILE_LOG_FIXTURE") and not os.environ.get("GITHUB_TOKEN"):
        print("log: GITHUB_TOKEN not set; keeping the existing log", file=sys.stderr)
        return 1
    commits = fetch()
    if not commits:
        print("log: no commits found; keeping the existing log", file=sys.stderr)
        return 0
    stamp = dt.datetime.now(TZ).strftime("%d %b %Y %H:%M WIB")
    (ASSETS / "log.svg").write_text(render(commits, stamp), encoding="utf-8")
    print("wrote log.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
