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
from theme import (ASSETS, THEMES, Iso, mix, panel, pixel_text, rect, slot, svg_doc, text, window)

LOGIN = os.environ.get("PROFILE_LOGIN", "ZainulArkaanAlinsi")
TZ = dt.timezone(dt.timedelta(hours=7))  # WIB
W = 1200
LINES = 7
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
    """Conventional-commit prefix -> the accent its chat tag uses."""
    head = message.split(":", 1)[0].split("(", 1)[0].lower() if ":" in message else ""
    return {"feat": "green", "fix": "red", "style": "violet", "docs": "blue", "refactor": "diamond",
            "chore": "gold", "test": "blue", "perf": "diamond", "init": "gold"}.get(head, "muted")


CSS = ("@keyframes toast{0%{transform:translateX(460px)}100%{transform:none}}"
       ".toast{animation:toast .8s .4s cubic-bezier(.2,1.1,.3,1) both}"
       "@keyframes shine{0%,80%{transform:translateX(-120px)}100%{transform:translateX(480px)}}"
       ".shine{animation:shine 5s 1.4s linear infinite}"
       "@keyframes line{from{opacity:0;transform:translateX(-14px)}to{opacity:1;transform:none}}"
       ".ln{animation:line .45s ease-out both}"
       "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
       ".blink{animation:blink 1.05s steps(1) infinite}")

CH = 7.22    # advance of one 12px monospace character


def render(theme, commits, stamp):
    t = THEMES[theme]
    shown = commits[:LINES][::-1]                       # chat reads oldest at top, newest at the bottom
    top, row = 156, 34
    h = top + row * LINES + 66
    out = [window(4, 4, W - 8, h, t, "~/commits --tail -f", f"live · synced {stamp}", "gold")]
    out.append(text(40, 66, "$", 12, t["green"], weight=700)
               + text(54, 66, "git log --all-repos --author=me", 12, t["muted"]))
    out.append(pixel_text("COMMIT LOG", 40, 80, 5, t["ink"], shadow=t["shadow"], shadow_op=t["px_shadow"]))
    repos = len({c["repo"] for c in commits})
    out.append(text(40, 138, f"every push lands here · {len(commits)} recent commits across {repos} repos",
                    12, t["muted"]))

    # chat lines
    cx, cw = 32, W - 64
    for i, c in enumerate(shown):
        y = top + i * row
        when = local(c["date"])
        newest = i == len(shown) - 1
        delay = .9 + i * .18
        stamp_s = f"[{when.strftime('%d %b %H:%M')}]"
        name = "<zainul>"
        tag = c["repo"]
        stats = f"+{c['additions']:,} -{c['deletions']:,}"
        used = len(stamp_s) + 1 + len(name) + 1 + len(tag) + 2 + 2 + len(stats) + 2
        msg = trim(c["message"], int(cw / CH) - used - 2)
        bg = (rect(cx, y, cw, row - 6, fill="#000000", op=.45 if t["dark"] else .80)
              + (rect(cx, y, 3, row - 6, fill=t["gold"]) if newest else ""))
        x = cx + 12
        parts = [text(x, y + 19, stamp_s, 12, "#8B93A0")]
        x += (len(stamp_s) + 1) * CH
        parts.append(text(x, y + 19, name, 12, "#7CE04A", weight=700))
        x += (len(name) + 1) * CH
        lang = c.get("color") or "#F2C14E"
        parts.append(rect(x, y + 9, 10, 10, fill=lang) + rect(x, y + 9, 10, 2, fill="#FFFFFF", op=.4))
        x += 16
        parts.append(text(x, y + 19, tag, 12, "#F2C14E", weight=700))
        x += (len(tag) + 1) * CH
        k = kind(c["message"])
        colour = "#FFFFFF" if k == "muted" else THEMES["dark"][k]
        parts.append(text(x, y + 19, msg, 12, colour if k != "muted" else "#EEF0F3"))
        sx = cx + cw - 12
        dele = f"-{c['deletions']:,}"
        parts.append(text(sx, y + 19, dele, 12, "#FF8A9A", anchor="end"))
        parts.append(text(sx - (len(dele) + 1) * CH, y + 19, f"+{c['additions']:,}", 12, "#7CE04A", anchor="end"))
        out.append(f'<g class="ln" style="animation-delay:{delay:.2f}s">{bg}{"".join(parts)}</g>')

    # chat input bar
    iy = top + row * LINES + 8
    out.append(rect(cx, iy, cw, 30, fill="#000000", op=.55 if t["dark"] else .85))
    out.append(text(cx + 12, iy + 20, "> git push origin main", 12, "#EEF0F3"))
    out.append(rect(cx + 12 + 22 * CH + 4, iy + 9, 7, 13, fill="#EEF0F3", extra=' class="blink"'))
    out.append(text(cx + cw - 12, iy + 20, "auto-refreshed by GitHub Actions", 11, "#8B93A0", anchor="end"))

    # advancement toast for the newest commit
    if commits:
        c = commits[0]
        tw_, th = 440, 78
        tx, ty = W - 4 - 32 - tw_, 52
        lang = c.get("color") or t["gold"]
        iso = Iso(tx + 39, ty + 35, 13)
        toast = [panel(tx, ty, tw_, th, THEMES["dark"], fill="#212121"),
                 slot(tx + 14, ty + 14, 50, 50, THEMES["dark"]),
                 iso.box(-.5, -.5, 0, 1, 1, 1, lang, top=mix(lang, "#FFFFFF", .3)),
                 text(tx + 78, ty + 30, "Advancement Made!", 13, "#F2C14E", weight=700),
                 text(tx + 78, ty + 52, trim(c["message"], 44), 12.5, "#FFFFFF"),
                 text(tx + 78, ty + 68, f"{c['repo']} · {c['oid']} · {local(c['date']).strftime('%d %b %H:%M')}",
                      10.5, "#9AA2AE"),
                 f'<clipPath id="tc{theme}"><rect x="{tx}" y="{ty}" width="{tw_}" height="{th}"/></clipPath>'
                 f'<g clip-path="url(#tc{theme})"><g class="shine">'
                 f'<polygon points="{tx},{ty} {tx + 40},{ty} {tx + 10},{ty + th} {tx - 30},{ty + th}"'
                 f' fill="#FFFFFF" opacity=".10"/></g></g>']
        out.append(f'<g class="toast">{"".join(toast)}</g>')
    newest = commits[0]["message"] if commits else "no commits yet"
    return svg_doc(W, h + 8, "".join(out), css=CSS,
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
    for name in THEMES:
        (ASSETS / f"log-{name}.svg").write_text(render(name, commits, stamp), encoding="utf-8")
        print("wrote", f"log-{name}.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
