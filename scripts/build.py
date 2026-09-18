"""Build every generated asset, then re-stamp the README.

The stamping is the part that matters for freshness. GitHub serves README images
through a caching image proxy keyed on the URL, so re-committing a file at the
same path can keep showing the old picture for a long time. Every local asset
reference therefore carries ?v=<content hash>: the URL changes exactly when the
bytes change, which busts the proxy without churning the README on no-op runs.

    GITHUB_TOKEN=... python scripts/build.py            # everything
    python scripts/build.py --skip-activity --skip-news # offline subset
"""
import datetime as dt
import hashlib
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from theme import ASSETS

ROOT = ASSETS.parent
README = ROOT / "README.md"
TZ = dt.timezone(dt.timedelta(hours=7))
LOCAL = re.compile(r'(?P<path>\./assets/[A-Za-z0-9._-]+\.svg)(?:\?v=(?P<v>[^"\')\s]*))?')
REMOTE = re.compile(r'(?P<url>https://raw\.githubusercontent\.com/[^"\')\s?]+\.svg)(?:\?v=[^"\')\s]*)?')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:10]


def stamp(text, day):
    missing = []

    def local(m):
        f = ROOT / m.group("path")[2:]
        if not f.exists():
            missing.append(m.group("path"))
            return m.group(0)
        return f"{m.group('path')}?v={digest(f)}"

    text = LOCAL.sub(local, text)
    text = REMOTE.sub(lambda m: f"{m.group('url')}?v={day}", text)
    return text, missing


def run(script, *args):
    cmd = [sys.executable, str(ROOT / "scripts" / script), *args]
    print(f"$ {' '.join(cmd[1:])}", flush=True)
    return subprocess.run(cmd, cwd=ROOT).returncode


def main():
    now = dt.datetime.now(TZ)
    built = now.strftime("%d %b %Y %H:%M WIB")
    failures = []

    from build_panels import build as build_panels
    build_panels(f"rebuilt {built}")
    print(f"panels: {len(list(ASSETS.glob('*.svg')))} assets on disk")

    if "--skip-activity" not in sys.argv:
        if not os.environ.get("GITHUB_TOKEN"):
            failures.append("activity: GITHUB_TOKEN is not set")
        elif run("build_activity.py"):
            failures.append("activity: generator failed")

    if "--skip-news" not in sys.argv and run("build_news.py"):
        failures.append("news: generator failed")

    text = README.read_text(encoding="utf-8")
    stamped, missing = stamp(text, now.strftime("%Y%m%d"))
    if missing:
        failures.append("README points at missing assets: " + ", ".join(sorted(set(missing))))
    if stamped != text:
        README.write_text(stamped, encoding="utf-8")
        print("README: asset versions re-stamped")
    else:
        print("README: asset versions already current")

    for f in failures:
        print("FAILED", f, file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
