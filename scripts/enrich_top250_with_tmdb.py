#!/usr/bin/env python3
"""Enrich the local Top 250 catalogue once with poster and Turkish TMDB metadata.

The runtime never needs this script or an API key: its output is written back
to ``imdb_top_250.json``.  The key is read only from the local ignored ``.env``
file (or the environment), so it cannot be committed with the catalogue.
"""

from __future__ import annotations

import json
import os
import ssl
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import certifi


ROOT = Path(__file__).resolve().parent.parent
CATALOGUE_PATH = ROOT / "imdb_top_250.json"
ENV_PATH = ROOT / ".env"
TMDB_API_BASE = "https://api.themoviedb.org/3"
POSTER_BASE = "https://image.tmdb.org/t/p/w500"


def load_key() -> str:
    key = os.environ.get("TMDB_API_KEY", "")
    if key:
        return key
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            name, separator, value = line.partition("=")
            if separator and name.strip() == "TMDB_API_KEY":
                return value.strip()
    return ""


def tmdb_get(path: str, params: dict[str, str]) -> dict:
    url = f"{TMDB_API_BASE}{path}?{urlencode(params)}"
    request = Request(url, headers={"Accept": "application/json"})
    secure_context = ssl.create_default_context(cafile=certifi.where())
    with urlopen(request, timeout=20, context=secure_context) as response:
        return json.loads(response.read().decode("utf-8"))


def choose_result(results: list[dict], year: int | None) -> dict | None:
    if not results:
        return None
    if year:
        for result in results:
            if str(result.get("release_date", ""))[:4] == str(year):
                return result
    return results[0]


def main() -> None:
    api_key = load_key()
    if not api_key:
        raise RuntimeError("TMDB_API_KEY was not found in .env or the environment.")

    payload = json.loads(CATALOGUE_PATH.read_text(encoding="utf-8"))
    genre_data = tmdb_get("/genre/movie/list", {"api_key": api_key, "language": "tr-TR"})
    genre_names = {genre["id"]: genre["name"] for genre in genre_data.get("genres", [])}
    enriched = 0
    credits_enriched = 0
    missed = []

    for index, movie in enumerate(payload["movies"], start=1):
        if not movie.get("tmdb_id"):
            params = {"api_key": api_key, "query": movie["title"], "language": "tr-TR", "include_adult": "false"}
            if movie.get("year"):
                params["year"] = str(movie["year"])
            try:
                data = tmdb_get("/search/movie", params)
            except OSError as error:
                missed.append(f"{movie['title']} ({error})")
                continue

            result = choose_result(data.get("results", []), movie.get("year"))
            if not result:
                missed.append(movie["title"])
                continue

            poster_path = result.get("poster_path")
            movie["tmdb_id"] = result.get("id")
            movie["poster_url"] = f"{POSTER_BASE}{poster_path}" if poster_path else None
            if result.get("overview"):
                movie["overview"] = result["overview"]
            tmdb_genres = [genre_names[genre_id] for genre_id in result.get("genre_ids", []) if genre_id in genre_names]
            if tmdb_genres:
                movie["genres"] = tmdb_genres

        if not movie.get("cast"):
            try:
                credits = tmdb_get(f"/movie/{movie['tmdb_id']}/credits", {"api_key": api_key, "language": "tr-TR"})
            except OSError as error:
                missed.append(f"{movie['title']} credits ({error})")
            else:
                movie["cast"] = [member["name"] for member in credits.get("cast", [])[:8] if member.get("name")]
                if not movie.get("directors"):
                    movie["directors"] = [
                        member["name"] for member in credits.get("crew", [])
                        if member.get("job") == "Director" and member.get("name")
                    ]
                credits_enriched += 1
        enriched += 1
        print(f"{index:>3}/250  {movie['title']}")
        time.sleep(0.08)

    payload["tmdb_enrichment"] = {
        "language": "tr-TR",
        "enriched_count": enriched,
        "credits_enriched_count": credits_enriched,
        "unmatched_titles": missed,
        "purpose": "poster and Turkish summary metadata stored locally for runtime use",
    }
    CATALOGUE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Enriched {enriched}/250 records.")
    if missed:
        print("Unmatched:", ", ".join(missed))


if __name__ == "__main__":
    main()
