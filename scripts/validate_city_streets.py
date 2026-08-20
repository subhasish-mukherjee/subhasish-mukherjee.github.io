#!/usr/bin/env python3
"""Validate the generated City Streets release using only the Python standard library."""

from __future__ import annotations

import json
import math
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: list[str] = []
        self.refs: list[str] = []

    def handle_starttag(self, _tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.append(values["id"] or "")
        for key in ("href", "src"):
            if values.get(key):
                self.refs.append(values[key] or "")


def load(path: Path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def json_slugs(directory: Path) -> set[str]:
    return {path.stem for path in directory.glob("*.json")}


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else "city-streets").resolve()
    api = root / "api"
    cities = load(api / "cities.json")
    slugs = [row["slug"] for row in cities]
    active = set(slugs)

    assert active and len(active) == len(slugs), "city slugs must be nonempty and unique"
    assert json_slugs(api / "city") == active, "per-city files do not match cities.json"
    assert json_slugs(api / "neighbors") == active, "neighbor files do not match cities.json"
    assert json_slugs(api / "neighborhoods") <= active, "orphan neighborhood file"

    for page in root.glob("*.html"):
        parser = PageParser()
        parser.feed(page.read_text(encoding="utf-8"))
        assert len(parser.ids) == len(set(parser.ids)), f"{page.name}: duplicate HTML id"
        for reference in parser.refs:
            parsed = urlsplit(reference)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            target = (page.parent / parsed.path).resolve()
            assert target.exists(), f"{page.name}: missing local reference {reference}"

    roses = load(api / "roses.json")
    assert {row["slug"] for row in roses} == active, "rose roster does not match cities.json"

    for row in cities:
        if row.get("region") != "north_america":
            assert row.get("walkscore") is None, f"unsupported Walk Score exported for {row['slug']}"
        report = load(api / "city" / f"{row['slug']}.json")
        assert report["meta"]["slug"] == row["slug"], f"wrong report at {row['slug']}"
        assert report["meta"]["report_version"] >= 16, f"stale report at {row['slug']}"
        weights = report["sphere"]["weights"]
        assert len(weights) == report["sphere"]["na"] * report["sphere"]["nz"]
        assert math.isclose(sum(weights), 1.0, abs_tol=1e-8), f"bad sphere weights at {row['slug']}"

        neighbors = load(api / "neighbors" / f"{row['slug']}.json")
        assert neighbors["slug"] == row["slug"]
        for values in neighbors["neighbors"].values():
            assert len(values) <= 5
            assert all(item["slug"] in active and item["slug"] != row["slug"] for item in values)

    for kind in ("sphere", "grid", "elevation", "js"):
        distances = load(api / "distances" / f"{kind}.json")
        order = distances["slugs"]
        matrix = distances["matrix"]
        assert set(order) == active and len(order) == len(active), f"{kind}: wrong roster"
        assert len(matrix) == len(order) and all(len(row) == len(order) for row in matrix)
        for i, row in enumerate(matrix):
            assert math.isclose(row[i], 0.0, abs_tol=1e-8), f"{kind}: nonzero diagonal"
            for j in range(i):
                assert math.isfinite(row[j]) and 0 <= row[j] <= 1 + 1e-9
                assert math.isclose(row[j], matrix[j][i], abs_tol=1e-9), f"{kind}: asymmetric"

    print(f"City Streets export valid: {len(active)} cities")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
