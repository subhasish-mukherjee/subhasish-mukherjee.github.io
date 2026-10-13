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


# Official commute modal share: record field -> flat key in cities.json (percent, 0-100).
COMMUTE_FIELDS = (("walk_share", "commute_walk"), ("bike_share", "commute_bike"),
                  ("transit_share", "commute_transit"), ("car_share", "commute_car"),
                  ("work_from_home_share", "commute_wfh"))
COMMUTE_SHARES = ("walk_share", "bike_share", "transit_share", "car_share",
                  "work_from_home_share", "other_share")
COMMUTE_TEXT = ("country", "period", "geography_name", "geography_type", "source_agency",
                "source_dataset", "source_label", "source_url")


def is_percent(value) -> bool:
    """None (not published) or a real number in [0, 100]; bools are not numbers here."""
    return value is None or (not isinstance(value, bool) and isinstance(value, (int, float))
                             and math.isfinite(value) and 0 <= value <= 100)


def check_commute(slug: str, record: dict, sources: dict) -> None:
    assert record.get("city_id") == slug, f"commute record keyed {slug} names another city"
    for key in COMMUTE_TEXT:
        assert isinstance(record.get(key), str) and record[key], f"{slug}: commute {key} missing"
    assert record["source_url"].startswith("https://"), f"{slug}: commute source is not https"
    assert record.get("source_id") in sources, f"{slug}: commute record cites an unknown source"
    assert record.get("basis") in ("all_workers", "commuters_only", "multi_response")
    values = [record.get(key) for key in COMMUTE_SHARES]
    assert all(is_percent(v) for v in values), f"{slug}: commute share outside 0-100"
    present = [v for v in values if v is not None]
    if record["basis"] != "multi_response":
        assert sum(present) <= 100.5, f"{slug}: commute shares exceed 100%"
        if record.get("other_share") is not None:
            assert abs(sum(present) - 100) <= 0.5, f"{slug}: commute shares do not sum to 100%"


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

    commute = load(api / "commute.json")
    commute_records = commute["cities"]
    assert set(commute_records) <= active, "commute record for a city not in cities.json"
    for slug, record in commute_records.items():
        check_commute(slug, record, commute["sources"])
    unavailable = commute.get("unavailable", {})
    assert set(unavailable) <= active, "commute reason for a city not in cities.json"
    assert not set(unavailable) & set(commute_records), "city both with and without commute data"
    assert all(isinstance(e.get("reason"), str) and e["reason"] for e in unavailable.values())

    for row in cities:
        if row.get("region") != "north_america":
            assert row.get("walkscore") is None, f"unsupported Walk Score exported for {row['slug']}"
        record = commute_records.get(row["slug"])
        for field, key in COMMUTE_FIELDS:
            expected = None if record is None else record[field]
            assert row.get(key) == expected, f"{row['slug']}: {key} differs from commute.json"
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

    print(f"City Streets export valid: {len(active)} cities, "
          f"{len(commute_records)} with commute modal share")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
