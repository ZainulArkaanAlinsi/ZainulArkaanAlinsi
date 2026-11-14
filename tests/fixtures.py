"""Deterministic fake data shaped exactly like the GitHub API responses, so the
renderers can be previewed and tested without a token or a network."""
import datetime as dt
import json
import random

LEVELS = ["NONE", "FIRST_QUARTILE", "SECOND_QUARTILE", "THIRD_QUARTILE", "FOURTH_QUARTILE"]


def activity(today=None, seed=7):
    rng = random.Random(seed)
    today = today or dt.date.today()
    start = today - dt.timedelta(days=today.weekday() + 1 + 52 * 7)   # a Sunday, 53 weeks back
    weeks, all_days, d = [], {}, start
    while d <= today:
        week = []
        for _ in range(7):
            if d > today:
                break
            busy = (d - start).days / 371
            n = 0 if rng.random() > .2 + busy * .6 else int(rng.expovariate(1 / (2 + busy * 14)))
            if (today - d).days < 8:
                n = max(n, 2 + rng.randrange(9))
            all_days[d.isoformat()] = n
            week.append({"date": d.isoformat(), "weekday": (d.weekday() + 1) % 7, "contributionCount": n,
                         "contributionLevel": LEVELS[min(4, (n + 3) // 4)]})
            d += dt.timedelta(days=1)
        weeks.append({"contributionDays": week})
    total = sum(x["contributionCount"] for w in weeks for x in w["contributionDays"])
    return {"created": "2024-07-01T00:00:00Z", "recent": {"totalContributions": total, "weeks": weeks},
            "all_days": all_days}


def commits(now=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    msgs = [("ZainulArkaanAlinsi", "feat: pixel terminal profile with minecraft hud", "Python", "#3572A5", 812, 340),
            ("laravel-kasir", "fix: rounding on receipt totals", "PHP", "#4F5D95", 14, 6),
            ("laravel-kasir", "feat: export daily report to pdf", "PHP", "#4F5D95", 220, 12),
            ("portfolio-next", "style: tighten hero spacing on mobile", "TypeScript", "#3178c6", 31, 28),
            ("flutter-notes", "feat: offline sync with sqlite", "Dart", "#00B4AB", 402, 51),
            ("portfolio-next", "chore: bump next to 15", "TypeScript", "#3178c6", 8, 8),
            ("flutter-notes", "init: flutter project", "Dart", "#00B4AB", 1210, 0)]
    out = []
    for i, (repo, msg, lang, colour, add, dele) in enumerate(msgs):
        out.append({"repo": repo, "message": msg, "language": lang, "color": colour, "additions": add,
                    "deletions": dele, "oid": f"{abs(hash(msg)) % 16 ** 7:07x}",
                    "date": (now - dt.timedelta(hours=i * 9 + 1)).isoformat()})
    return out


if __name__ == "__main__":
    import sys
    json.dump(activity() if sys.argv[1] == "activity" else commits(), sys.stdout)
