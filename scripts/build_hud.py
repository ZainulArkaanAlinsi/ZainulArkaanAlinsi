"""Game-HUD panels fed by real GitHub data: the player bar and the commit log.

  player-*.svg   hearts = current streak (capped at 10), XP bar = contributions,
                 100 contributions per level. Nothing here is invented: the level
                 is total // 100 and the bar is the remainder.
  commits-*.svg  a chat-log of the latest public pushes, newest first.

    GITHUB_TOKEN=... python scripts/build_hud.py

Privacy switches (environment):
  PROFILE_LOG_HIDE_REPOS=repo-a,repo-b   never list these repos
  PROFILE_LOG_MESSAGES=0                 list repo + time only, no commit text
Commit subjects that mention secrets or vulnerabilities are always withheld.
"""
import datetime as dt
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import ASSETS, THEMES, Iso, mix, pixel_text, pixel_width, rect, svg_doc, text
from build_panels import chrome
from build_activity import LOGIN, TZ, fetch, streaks

W, PAD = 1200, 34
PER_LEVEL = 100            # contributions per level
MAX_HEARTS = 10
LOG_ROWS = 7
LOG_DAYS = 7               # window for the "pushed N times" toast
MSG_MAX = 68               # keeps the text clear of the NEW badge at the right edge

# ------------------------------------------------------------------------- data
SENSITIVE = re.compile(
    r"secret|token|passw|credential|api[-_ ]?key|private[-_ ]?key|vuln|cve-|exploit|"
    r"injection|bypass|leak|redact|hash|\.env|fail-closed", re.I)
CONVENTIONAL = re.compile(r"^(?P<tag>[a-zA-Z]+)(?:\([^)]*\))?(?P<bang>!)?:\s*(?P<msg>.+)$")
TAG_ACCENT = {"feat": "green", "fix": "red", "test": "blue", "docs": "violet",
              "chore": "amber", "refactor": "amber", "perf": "amber", "build": "amber",
              "ci": "amber", "style": "amber"}


def level_xp(total, per=PER_LEVEL):
    """(level, xp into this level, xp the level needs)."""
    total = max(0, int(total))
    return total // per, total % per, per


def hearts_full(streak, cap=MAX_HEARTS):
    return max(0, min(cap, int(streak)))


def split_subject(message):
    """First line of a commit message -> (tag, text). Untagged commits are 'push'."""
    line = (message or "").strip().splitlines()[0].strip() if (message or "").strip() else ""
    m = CONVENTIONAL.match(line)
    if m:
        return m.group("tag").lower()[:8], m.group("msg").strip()
    return "push", line


def is_merge(subject):
    return subject.lower().startswith(("merge branch", "merge pull request", "merge remote"))


def truncate(s, n=MSG_MAX):
    return s if len(s) <= n else s[:n - 1].rstrip() + "…"


def build_rows(events, get_message, now, hide_repos=(), limit=LOG_ROWS, show_messages=True):
    """Newest-first log rows from raw /events payloads.

    get_message(repo, sha) -> commit message or None; injected so tests stay offline.
    Returns (rows, pushes_in_window).
    """
    hide = {h.strip().lower() for h in hide_repos if h.strip()}
    pushes, rows, seen = 0, [], set()
    for ev in sorted((e for e in events if e.get("type") == "PushEvent"),
                     key=lambda e: e.get("created_at", ""), reverse=True):
        repo = ev["repo"]["name"].split("/", 1)[-1]
        if repo.lower() in hide:
            continue
        at = dt.datetime.fromisoformat(ev["created_at"].replace("Z", "+00:00"))
        sha = ev.get("payload", {}).get("head")
        if not sha or sha in seen:
            continue
        seen.add(sha)
        if now - at <= dt.timedelta(days=LOG_DAYS):
            pushes += 1
        if len(rows) >= limit:
            continue
        tag, body = "push", ""
        if show_messages:
            msg = get_message(ev["repo"]["name"], sha)
            if msg is None:
                continue
            tag, body = split_subject(msg)
            if is_merge(body):
                continue
            if SENSITIVE.search(body):
                tag, body = "push", "details withheld"
        rows.append({"at": at, "repo": repo, "tag": tag, "text": truncate(body),
                     "new": now - at <= dt.timedelta(hours=24)})
    return rows, pushes


def api(path, token=None):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-hud"}
    if token:
        headers["Authorization"] = f"bearer {token}"
    with urllib.request.urlopen(urllib.request.Request("https://api.github.com" + path, headers=headers),
                                timeout=30) as r:
        return json.load(r)


def fetch_events(token=None):
    return api(f"/users/{LOGIN}/events/public?per_page=100", token)


def fetch_message(repo, sha, token=None):
    try:
        return api(f"/repos/{repo}/commits/{sha}", token)["commit"]["message"]
    except Exception:
        return None


# ---------------------------------------------------------------------- pixel art
HEART = ["011000110", "111101111", "111111111", "111111111", "011111110", "001111100",
         "000111000", "000010000"]
HEART_PX = {(x, y) for y, row in enumerate(HEART) for x, c in enumerate(row) if c == "1"}
HEART_EDGE = {(x + dx, y + dy) for (x, y) in HEART_PX for dx in (-1, 0, 1) for dy in (-1, 0, 1)} - HEART_PX


def heart(x, y, s, fill, outline, empty=False, shine="#FFFFFF"):
    """A 9x8 pixel heart. Outline first, then body, then one highlight pixel."""
    cells = [rect(x + (ex + 1) * s, y + (ey + 1) * s, s, s, fill=outline) for ex, ey in sorted(HEART_EDGE)]
    cells += [rect(x + (px + 1) * s, y + (py + 1) * s, s, s, fill=fill, op=None) for px, py in sorted(HEART_PX)]
    if not empty:
        cells.append(rect(x + 2 * s, y + 2 * s, s, s, fill=shine, op=.85))
    return "".join(cells)


# ----------------------------------------------------------------------- player
PLAYER_CSS = (
    "@keyframes rg{0%{transform:translateY(0)}5%{transform:translateY(-5px)}10%,100%{transform:translateY(0)}}"
    ".rg{animation:rg 4.2s steps(2) infinite}"
    "@keyframes shim{0%{transform:translateX(-60px)}70%,100%{transform:translateX(var(--fw,700px))}}"
    ".shim{animation:shim 3.6s linear infinite}"
    "@keyframes orb{0%{transform:translateY(0);opacity:0}15%{opacity:1}100%{transform:translateY(-30px);opacity:0}}"
    ".orb{animation:orb 2.4s steps(6) infinite}"
    "@keyframes bob{0%,100%{opacity:1}50%{opacity:.2}}"
    "@media (prefers-reduced-motion:reduce){.rg,.shim,.orb{animation:none}}")


def player(t, total, streak, stamp):
    level, into, need = level_xp(total)
    full = hearts_full(streak)
    y0, h = 8, 176
    hx, bx = 340, 340
    bw, bh = 790, 20
    by = y0 + 108
    fw = round(bw * into / need)
    green = t["green"]
    out_ln = "#000000" if t["px_shadow"] > .3 else mix(t["ink"], t["bg"], .55)

    body = [rect(0, 0, W, h + PAD, fill=t["bg"]),
            chrome(t, PAD, y0, W - PAD * 2, h, "~/player --stats", f"synced {stamp}", "green", "player",
                   glows=[(.08, .3, 300, "green"), (.92, .8, 280, "red")]),
            pixel_text("PLAYER", PAD + 28, y0 + 54, 3, t["ink"], shadow=t["shadow"], shadow_op=t["px_shadow"]),
            text(PAD + 28, y0 + 54 + 21 + 20, f"@{LOGIN}", 12, t["muted"]),
            text(PAD + 28, y0 + 54 + 21 + 38, "hearts = streak · xp = contributions", 11, t["muted"])]

    for i in range(MAX_HEARTS):
        on = i < full
        body.append(f'<g class="rg" style="animation-delay:{i * .18:.2f}s">'
                    + heart(hx + i * 36, y0 + 52, 3, t["red"] if on else mix(t["bg"], t["ink"], .10),
                            out_ln, empty=not on) + "</g>")

    streak_lbl = f"STREAK {streak}" if streak else "NO STREAK YET"
    body.append(pixel_text(streak_lbl, bx + bw - pixel_width(streak_lbl, 2), y0 + 62, 2, t["ink"],
                           shadow=t["shadow"], shadow_op=t["px_shadow"]))

    # the level number rides the middle of the bar, exactly where Minecraft puts it
    lv = str(level)
    body.append(pixel_text(lv, bx + bw / 2 - pixel_width(lv, 4) / 2, y0 + 70, 4, green,
                           shadow="#000000", shadow_op=.9 if t["px_shadow"] > .3 else .35))

    clip = "xpclip"
    body += [rect(bx - 3, by - 3, bw + 6, bh + 6, fill=out_ln),
             rect(bx, by, bw, bh, fill=mix(t["bg"], t["ink"], .12)),
             f'<clipPath id="{clip}"><rect x="{bx}" y="{by}" width="{fw}" height="{bh}"/></clipPath>',
             rect(bx, by, fw, bh, fill=green),
             rect(bx, by, fw, 5, fill="#FFFFFF", op=.28),
             rect(bx, by + bh - 5, fw, 5, fill="#000000", op=.22),
             f'<g clip-path="url(#{clip})"><rect class="shim" style="--fw:{fw + 20}px" x="{bx}" y="{by}"'
             f' width="26" height="{bh}" fill="#FFFFFF" opacity=".30"/></g>']
    for k in range(1, 20):                                             # notches, like the real bar
        body.append(rect(bx + bw * k / 20, by, 2, bh, fill="#000000", op=.20))
    for k, dx in enumerate((-6, 4, 12)):                               # xp orbs lifting off the tip
        body.append(rect(bx + fw + dx, by - 4, 6, 6, fill=green, op=None,
                         extra=f' class="orb" style="animation-delay:{k * .8:.1f}s"'))

    body.append(text(bx, by + bh + 26, f"{into} / {need} XP", 12, t["ink"], weight=500))
    body.append(text(bx + bw, by + bh + 26,
                     f"{need - into} more for level {level + 1} · {need} contributions per level",
                     12, t["muted"], anchor="end"))
    return svg_doc(W, h + PAD, "".join(body), css=PLAYER_CSS,
                   label=f"Player level {level}: {into} of {need} experience, streak of {streak} days")


# -------------------------------------------------------------------- commit log
LOG_CSS = (
    # rows stay visible; a highlight scans down them like new chat lines arriving
    "@keyframes flash{0%{opacity:.16}8%{opacity:.04}100%{opacity:.04}}"
    ".flash{animation:flash 6s steps(3) infinite}"
    "@keyframes bob{0%,100%{opacity:1}50%{opacity:.15}}"
    ".bob{animation:bob 1.1s steps(1) infinite}"
    "@keyframes pop{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}"
    ".pop{animation:pop 2.4s steps(2) infinite}"
    "@media (prefers-reduced-motion:reduce){.flash,.bob,.pop{animation:none}}")
COL_TIME = PAD + 36
COL_TAG = COL_TIME + 110
COL_REPO = COL_TAG + 124          # widest tag chip is "REFACTOR" = 110px
COL_MSG = COL_REPO + 240          # repo names are cut at 28 characters


def toast(t, x, y, pushes):
    """Advancement-style box, top right of the panel."""
    w, h = 312, 58
    iso = Iso(x + 30, y + 30, 11)
    out = [rect(x, y, w, h, fill=t["amber"]), rect(x + 2, y + 2, w - 4, h - 4, fill="#140F1E"),
           f'<g class="pop">{iso.box(-.5, -.5, -.5, 1, 1, 1, t["green"], top=mix(t["green"], "#FFFFFF", .25))}</g>',
           pixel_text("ADVANCEMENT MADE!", x + 56, y + 11, 2, t["amber"], shadow="#000000", shadow_op=.7),
           text(x + 56, y + 43, f"Pushed {pushes} time{'s' if pushes != 1 else ''} in {LOG_DAYS} days",
                11.5, "#FFFFFF")]
    return "".join(out)


def commits(t, rows, pushes, stamp):
    n = max(1, len(rows))
    y0, h = 8, 120 + n * 38 + 44
    body = [rect(0, 0, W, h + PAD, fill=t["bg"]),
            chrome(t, PAD, y0, W - PAD * 2, h, "~/events --push --public", f"synced {stamp}", "blue",
                   "commits", glows=[(.06, .2, 300, "blue"), (.94, .85, 300, "green")]),
            pixel_text("COMMIT LOG", PAD + 28, y0 + 54, 3, t["ink"], shadow=t["shadow"], shadow_op=t["px_shadow"]),
            text(PAD + 28, y0 + 54 + 21 + 20, "latest pushes to public repos · newest first", 12, t["muted"])]
    if pushes:
        body.append(toast(t, W - PAD - 28 - 312, y0 + 44, pushes))

    if not rows:
        body.append(text(COL_TIME, y0 + 142, "no public pushes yet — the next one shows up here", 13, t["muted"]))
    for i, r in enumerate(rows):
        y = y0 + 112 + i * 38
        accent = TAG_ACCENT.get(r["tag"])
        col = t[accent] if accent else t["muted"]
        stamp_txt = r["at"].astimezone(TZ).strftime("%d %b %H:%M").lstrip("0")
        tag = r["tag"].upper()
        tw = pixel_width(tag, 2) + 16
        row = [rect(PAD + 20, y, W - PAD * 2 - 40, 32, fill=t["ink"], op=.04,
                    extra=f' class="flash" style="animation-delay:{i * .5:.1f}s"'),
               rect(PAD + 20, y, 3, 32, fill=col),
               text(COL_TIME, y + 20, stamp_txt, 12, t["muted"]),
               rect(COL_TAG, y + 5, tw, 22, fill=col, op=.18),
               pixel_text(tag, COL_TAG + 8, y + 9, 2, col, shadow=t["shadow"], shadow_op=t["px_shadow"] * .6),
               text(COL_REPO, y + 20, r["repo"] if len(r["repo"]) <= 28 else r["repo"][:27] + "…",
                    12.5, t["ink"], weight=600)]
        if r["text"]:
            row.append(text(COL_MSG, y + 20, r["text"], 12.5, t["muted"]))
        if r["new"]:
            row.append(f'<g class="bob">{pixel_text("NEW", W - PAD - 28 - pixel_width("NEW", 2) - 8, y + 9, 2, t["green"], shadow=t["shadow"], shadow_op=t["px_shadow"] * .6)}</g>')
        body.append("".join(row))

    py = y0 + 112 + max(len(rows), 1) * 38 + 12
    body.append(text(COL_TIME, py + 14, "> awaiting next push", 12.5, t["green"], weight=600))
    body.append(f'<rect class="bob" x="{COL_TIME + 156}" y="{py + 3}" width="8" height="14" fill="{t["green"]}"/>')
    return svg_doc(W, h + PAD, "".join(body), css=LOG_CSS,
                   label=f"Latest public pushes: {', '.join(r['repo'] for r in rows[:3]) or 'none yet'}")


# ------------------------------------------------------------------------ build
def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    token = os.environ.get("GITHUB_TOKEN")
    now = dt.datetime.now(dt.timezone.utc)
    stamp = now.astimezone(TZ).strftime("%d %b %Y %H:%M WIB")
    failed = False

    # --- commit log: public data only; a hiccup keeps whatever is already committed
    try:
        hide = os.environ.get("PROFILE_LOG_HIDE_REPOS", "").split(",")
        show = os.environ.get("PROFILE_LOG_MESSAGES", "1") != "0"
        rows, pushes = build_rows(fetch_events(token), lambda r, s: fetch_message(r, s, token), now,
                                  hide_repos=hide, show_messages=show)
        from build_editorial import commits as glass_commits
        (ASSETS / "commits-dark.svg").write_text(glass_commits(rows, pushes, stamp), encoding="utf-8")
        print("wrote commits-dark.svg", f"({len(rows)} rows, {pushes} pushes/{LOG_DAYS}d)")
    except Exception as e:
        failed = True
        print(f"commits: kept existing panel ({e})", file=sys.stderr)

    # first run with no network must not leave the README pointing at nothing
    if not (ASSETS / "commits-dark.svg").exists():
        from build_editorial import commits as glass_commits
        (ASSETS / "commits-dark.svg").write_text(glass_commits([], 0, "offline"), encoding="utf-8")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
