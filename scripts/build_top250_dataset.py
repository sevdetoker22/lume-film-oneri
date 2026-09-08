#!/usr/bin/env python3
"""Build Lûme's compact IMDb Top 250 catalogue from two downloaded public CSVs.

The source files intentionally live in ``.imdb/`` because they are input
artifacts.  The generated JSON is the small, application-facing catalogue.
It contains only the fields that the recommendation, chat and quiz features
need; it does not retain reviews, images galleries or other bulk scrape data.
"""

from __future__ import annotations

import ast
import csv
import json
import re
from datetime import date
from difflib import get_close_matches
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CURRENT_RANKING_PATH = ROOT / ".imdb" / "top250-2026-source.csv"
DETAILS_PATH = ROOT / ".imdb" / "top250-2025-details.csv"
OUTPUT_PATH = ROOT / "imdb_top_250.json"

RANKING_SOURCE = "https://zenodo.org/records/19385836"
DETAILS_SOURCE = "https://github.com/ArshaAsh15/IMDb-Top-250-Movies"


def key(title: str, year: str = "") -> str:
    normalized = re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()
    return f"{normalized}|{year.strip()}"


def split_csv(value: str | None) -> list[str]:
    return [part.strip() for part in (value or "").split(",") if part.strip() and part.strip() != "Not Available"]


def parse_literal(value: str | None) -> dict:
    try:
        parsed = ast.literal_eval(value or "")
    except (SyntaxError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def read_rows(path: Path, encoding: str) -> list[dict[str, str]]:
    with path.open(encoding=encoding, newline="") as source:
        return list(csv.DictReader(source))


def details_index(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {key(row["name"], row["year"]): row for row in rows}


def matching_details(
    row: dict[str, str],
    indexed: dict[str, dict[str, str]],
) -> dict[str, str] | None:
    exact = indexed.get(key(row["Title"], row["Year"]))
    if exact:
        return exact

    same_title = [candidate for candidate in indexed if candidate.rsplit("|", 1)[0] == key(row["Title"]).rsplit("|", 1)[0]]
    if same_title:
        return indexed[same_title[0]]

    candidates = get_close_matches(key(row["Title"]), [candidate.rsplit("|", 1)[0] for candidate in indexed], n=1, cutoff=0.92)
    if candidates:
        matched_title = candidates[0]
        for candidate, detail in indexed.items():
            if candidate.rsplit("|", 1)[0] == matched_title:
                return detail
    return None


def awards_summary(row: dict[str, str]) -> str:
    return parse_literal(row.get("Total_Awards")).get("Total_Awards", "")


def build() -> dict:
    ranking_rows = read_rows(CURRENT_RANKING_PATH, "utf-8-sig")
    detail_rows = read_rows(DETAILS_PATH, "latin-1")
    details = details_index(detail_rows)
    movies = []
    unmatched = []

    for rank, row in enumerate(ranking_rows, start=1):
        detail = matching_details(row, details)
        reviews = parse_literal(row.get("Data_reviews"))
        if not detail:
            unmatched.append(row["Title"])

        title = row["Title"].strip()
        year = row["Year"].strip()
        movies.append(
            {
                "rank": rank,
                "title": title,
                "year": int(year) if year.isdigit() else None,
                "imdb_rating": float(row["Rating"]) if row.get("Rating") else None,
                "vote_count": row.get("Vote_Count", "").strip().strip("() "),
                "runtime": row.get("Duration", "").strip(),
                "certificate": row.get("Rating_age", "").strip(),
                "countries": reviews.get("Countries", []),
                "directors": reviews.get("Director", []) or split_csv(detail.get("directors") if detail else ""),
                "writers": reviews.get("Writers", []) or split_csv(detail.get("writers") if detail else ""),
                "cast": split_csv(detail.get("casts") if detail else "")[:8],
                "genres": split_csv(detail.get("genre") if detail else ""),
                "tagline": (detail.get("tagline", "").strip() if detail else ""),
                "overview": (detail.get("tagline", "").strip() if detail else ""),
                "awards": awards_summary(row),
                "imdb_url": "https://www.imdb.com/find/?q=" + title.replace(" ", "+"),
                "poster_url": None,
            }
        )

    if len(movies) != 250:
        raise RuntimeError(f"Expected 250 ranking rows, found {len(movies)}")

    return {
        "schema_version": 1,
        "generated_on": date.today().isoformat(),
        "catalogue": "IMDb Top 250",
        "sources": [
            {
                "purpose": "ranking, ratings, votes, runtime, certificate, awards",
                "url": RANKING_SOURCE,
                "published": "2026-04-02",
            },
            {
                "purpose": "genres, cast, director, writers and taglines",
                "url": DETAILS_SOURCE,
                "snapshot": "2025",
            },
        ],
        "record_count": len(movies),
        "detail_match_count": len(movies) - len(unmatched),
        "unmatched_detail_titles": unmatched,
        "movies": movies,
    }


if __name__ == "__main__":
    payload = build()
    OUTPUT_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {payload['record_count']} records to {OUTPUT_PATH.name}.")
    print(f"Detail matches: {payload['detail_match_count']}/250")
    if payload["unmatched_detail_titles"]:
        print("Unmatched:", ", ".join(payload["unmatched_detail_titles"]))
