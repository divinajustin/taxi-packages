"""Build the static taxi-package site into dist/.

Usage:
    python build.py            # build once
    python build.py --serve    # build, then preview at http://localhost:8000
"""
import re
import shutil
import sys
from datetime import date
from pathlib import Path
from urllib.parse import quote

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
DIST = ROOT / "dist"


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def rupees(value: int) -> str:
    """Indian digit grouping: 125000 -> 1,25,000."""
    s = str(int(value))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    head = re.sub(r"(\d)(?=(\d{2})+$)", r"\1,", head)
    return f"{head},{tail}"


def load(name):
    with open(ROOT / name, encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate(site, packages):
    vehicle_names = {v["name"] for v in site["vehicles"]}
    for p in packages:
        for key in ("name", "from", "to", "days", "prices"):
            if key not in p:
                sys.exit(f"Package {p.get('name', '?')!r} is missing '{key}'")
        unknown = set(p["prices"]) - vehicle_names
        if unknown:
            sys.exit(f"Package {p['name']!r} uses unknown vehicle(s): {', '.join(unknown)}")
        if p.get("image") and not (ROOT / "static/images" / p["image"]).exists():
            sys.exit(f"Image not found for {p['name']!r}: static/images/{p['image']}")


def build():
    site = load("site.yaml")
    packages = load("packages.yaml")
    validate(site, packages)

    vehicle_order = [v["name"] for v in site["vehicles"]]
    for p in packages:
        p["slug"] = slugify(p["name"])
        p["min_price"] = min(p["prices"].values())
        p["price_rows"] = [(v, p["prices"][v]) for v in vehicle_order if v in p["prices"]]
        p["wa_link"] = (
            f"https://wa.me/{site['whatsapp']}?text="
            + quote(f"Hi, I'd like to book the {p['name']} package ({p['days']} day). "
                    "Travel date: ___  Number of people: ___")
        )

    site["wa_general"] = f"https://wa.me/{site['whatsapp']}?text=" + quote(
        "Hi, I'd like to know about your taxi packages."
    )
    site["url"] = site["url"].rstrip("/")

    env = Environment(
        loader=FileSystemLoader(ROOT / "templates"),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.filters["rupees"] = rupees
    ctx = {"site": site, "packages": packages, "year": date.today().year}

    shutil.rmtree(DIST, ignore_errors=True)
    shutil.copytree(ROOT / "static", DIST / "static")

    (DIST / "index.html").write_text(
        env.get_template("index.html").render(**ctx, page_path="/"), encoding="utf-8"
    )
    for p in packages:
        out = DIST / "packages" / p["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(
            env.get_template("package.html").render(
                **ctx, p=p, page_path=f"/packages/{p['slug']}/"
            ),
            encoding="utf-8",
        )

    paths = ["/"] + [f"/packages/{p['slug']}/" for p in packages]
    sitemap = "\n".join(f"  <url><loc>{site['url']}{path}</loc></url>" for path in paths)
    (DIST / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{sitemap}\n</urlset>\n",
        encoding="utf-8",
    )
    (DIST / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\nSitemap: {site['url']}/sitemap.xml\n", encoding="utf-8"
    )
    print(f"Built {len(packages)} packages into {DIST}")


if __name__ == "__main__":
    build()
    if "--serve" in sys.argv:
        import functools
        import http.server

        handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DIST)
        print("Preview at http://localhost:8000  (Ctrl+C to stop)")
        http.server.ThreadingHTTPServer(("", 8000), handler).serve_forever()
