"""Commit log: the latest pushes, rendered as an in-game chat with an
"Advancement Made!" toast for the newest commit.

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
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import mc  # noqa: E402
from build_panels import CARD_H  # noqa: E402
from gui import AQUA, GOLD, GRAY, GREEN, HALF, RED, YELLOW, mc_pixel, mc_text, rect, svg  # noqa: E402
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


def kind(message):
    """Conventional-commit prefix -> the game's chat colour for it."""
    head = message.split(":", 1)[0].split("(", 1)[0].lower() if ":" in message else ""
    return {"feat": GREEN, "fix": RED, "style": "#FF55FF", "docs": AQUA, "refactor": AQUA,
            "chore": GOLD, "test": AQUA, "perf": AQUA, "init": GOLD}.get(head, "#FFFFFF")


CSS = ("@keyframes toast{0%{transform:translateX(360px)}100%{transform:none}}"
       ".toast{animation:toast .8s .4s cubic-bezier(.2,1.1,.3,1) both}"
       "@keyframes line{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}"
       ".ln{animation:line .4s ease-out both}"
       "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
       ".blink{animation:blink 1.05s steps(1) infinite}")

CH = 7.22    # advance of one 12px monospace character
LINES = 6


def backdrop(w, h):
    from build_panels import panorama
    img = mc.blur(panorama(w + 20, h, seed=29), 5)
    return Image.fromarray((np.asarray(img, float) * .5).astype(np.uint8)).crop((0, 0, w * 2, h * 2))


def render(commits, stamp):
    w, h = HALF, CARD_H
    out = [mc.image(mc.png_uri(backdrop(w, h), 128), 0, 0, w, h)]
    out.append(mc_pixel("COMMIT LOG", 20, 22, 3))
    out.append(mc_text(20, 64, f"{len(commits)} recent commits · {len({c['repo'] for c in commits})} repos", 12, "#E6E6E6"))
    out.append(mc_text(20, 82, f"synced {stamp}", 11, "#E6E6E6"))

    # chat, newest at the bottom, the way the game scrolls it
    shown = commits[:LINES][::-1]
    row = 44
    top = h - 58 - row * len(shown)
    cols = int((w - 48) / CH)
    for i, c in enumerate(shown):
        y = top + i * row
        newest = i == len(shown) - 1
        name = "<zainul> "
        msg = trim(c["message"], cols - len(name))
        meta = (f"  {c['repo']} · {c['oid']} · +{c['additions']:,} -{c['deletions']:,} · "
                f"{local(c['date']).strftime('%d %b %H:%M')}")
        g = [rect(12, y, w - 24, row - 2, "#000000", .5)]
        if newest:
            g.append(rect(12, y, 3, row - 2, YELLOW))
        g.append(mc_text(22, y + 18, name, 12, "#FFFFFF"))
        g.append(mc_text(22 + len(name) * CH, y + 18, msg, 12, kind(c["message"])))
        g.append(mc_text(22, y + 35, trim(meta, cols), 11, GRAY))
        out.append(f'<g class="ln" style="animation-delay:{.9 + i * .2:.2f}s">{"".join(g)}</g>')

    # the chat input line
    iy = h - 44
    out.append(rect(12, iy, w - 24, 30, "#000000", .62))
    out.append(mc_text(22, iy + 20, "> git push origin main", 12, "#FFFFFF"))
    out.append(rect(22 + 22 * CH + 4, iy + 9, 7, 13, "#FFFFFF", extra=' class="blink"'))

    # advancement toast for the newest commit
    if commits:
        c = commits[0]
        tw_, th = 300, 64
        tx, ty = w - 14 - tw_, 16
        lang = c.get("color") or "#F2C14E"
        toast = [rect(tx, ty, tw_, th, "#000000"), rect(tx + 2, ty + 2, tw_ - 4, th - 4, "#212121"),
                 rect(tx + 2, ty + 2, tw_ - 4, 2, "#555555"),
                 mc.image(mc.png_uri(mc.icon("emerald_block", 64)), tx + 12, ty + 14, 36, 36),
                 mc_text(tx + 58, ty + 24, "Advancement Made!", 13, YELLOW, weight=700),
                 mc_text(tx + 58, ty + 44, trim(c["message"], 32), 12, "#FFFFFF"),
                 rect(tx + tw_ - 14, ty + 8, 6, 6, lang)]
        out.append(f'<g class="toast">{"".join(toast)}</g>')
    out.append(f'<rect x="1" y="1" width="{w - 2}" height="{h - 2}" fill="none" stroke="#000" stroke-width="2"/>')
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
    (ASSETS / "chat.svg").write_text(render(commits, stamp), encoding="utf-8")
    print("wrote chat.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
