"""Local Qwen3-powered search interface for the entertainment QA data."""

from __future__ import annotations

import json
import os
import re
import threading
import csv
import random
import ssl
import time
import base64
import gzip
import sqlite3
import secrets
from datetime import datetime, timedelta
from functools import lru_cache, wraps
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

import numpy as np
from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

DATA_PATH = Path(__file__).with_name("entertainment_qa.jsonl")
MOVIES_PATH = Path(__file__).with_name("movies.json")
TOP_250_PATH = Path(__file__).with_name("imdb_top_250.json")
ENV_PATH = Path(__file__).with_name(".env")
QUIZ_FILES = {
    "Filmler": "category_movies.csv",
    "Ünlüler": "category_celebrities.csv",
}
MODEL_ID = "mlx-community/Qwen3-1.7B-4bit"
EMBEDDING_MODEL_ID = "intfloat/multilingual-e5-small"
CACHE_PATH = Path(__file__).with_name(".cache") / "multilingual-e5-small.npy"
TRANSLATION_CACHE_PATH = Path(__file__).with_name(".cache") / "quiz_translations.json"
MAX_CANDIDATES = 3
SEMANTIC_CONFIDENCE_THRESHOLD = 0.55
TMDB_API_BASE = "https://api.themoviedb.org/3"

app = Flask(__name__)


def load_local_env() -> None:
    """Load development secrets without adding a runtime dependency."""
    if not ENV_PATH.exists():
        return
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        if separator and key.strip() and not key.lstrip().startswith("#"):
            os.environ.setdefault(key.strip(), value.strip())


load_local_env()
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", "")
GOOGLE_OAUTH_ENABLED = bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET)
GOOGLE_AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v3/userinfo"
DATABASE_PATH = Path(os.environ.get("FILM_SITE_DB", Path(__file__).with_name(".cache") / "film-site.sqlite3"))
SESSION_SECRET_PATH = Path(__file__).with_name(".cache") / "flask-session-secret"


def _session_secret() -> str:
    configured = os.environ.get("FLASK_SECRET_KEY")
    if configured:
        return configured
    SESSION_SECRET_PATH.parent.mkdir(exist_ok=True)
    if SESSION_SECRET_PATH.exists():
        return SESSION_SECRET_PATH.read_text(encoding="utf-8").strip()
    generated = secrets.token_hex(32)
    SESSION_SECRET_PATH.write_text(generated, encoding="utf-8")
    try:
        SESSION_SECRET_PATH.chmod(0o600)
    except OSError:
        pass
    return generated


app.config.update(
    SECRET_KEY=_session_secret(),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
)


def database_connection() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_database() -> None:
    with database_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT COLLATE NOCASE,
                email TEXT NOT NULL COLLATE NOCASE UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                movie_id INTEGER NOT NULL,
                movie_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE (user_id, movie_id)
            );
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                movie_id INTEGER NOT NULL,
                movie_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE (user_id, movie_id)
            );
            CREATE TABLE IF NOT EXISTS blog_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                movie_id INTEGER NOT NULL,
                movie_title TEXT NOT NULL,
                movie_poster TEXT,
                movie_backdrop TEXT,
                movie_year TEXT,
                post_type TEXT NOT NULL DEFAULT 'Film Üzerine',
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                view_count INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS blog_post_likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE (post_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS blog_post_saves (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE (post_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS blog_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES blog_posts(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        # blog_posts önceden var olan kurulumlarda bu kolonlar olmadan oluşturulmuş
        # olabilir; CREATE TABLE IF NOT EXISTS bunları eklemez, bu yüzden elle taşınır.
        existing_columns = {row["name"] for row in connection.execute("PRAGMA table_info(blog_posts)")}
        if "movie_backdrop" not in existing_columns:
            connection.execute("ALTER TABLE blog_posts ADD COLUMN movie_backdrop TEXT")
        if "post_type" not in existing_columns:
            connection.execute("ALTER TABLE blog_posts ADD COLUMN post_type TEXT NOT NULL DEFAULT 'Film Üzerine'")
        if "view_count" not in existing_columns:
            connection.execute("ALTER TABLE blog_posts ADD COLUMN view_count INTEGER NOT NULL DEFAULT 0")
        # users tablosuna Google OAuth için eklenen kolonlar; mevcut kurulumlarda
        # elle taşınır. password_hash NOT NULL kalır — Google ile oluşan hesaplar
        # kullanılamayacak rastgele bir hash alır, ayrı bir kod yolu gerekmez.
        existing_user_columns = {row["name"] for row in connection.execute("PRAGMA table_info(users)")}
        if "google_id" not in existing_user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN google_id TEXT")
        if "avatar_url" not in existing_user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
        if "username" not in existing_user_columns:
            connection.execute("ALTER TABLE users ADD COLUMN username TEXT COLLATE NOCASE")
        connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)")
        # username NULL olabilir (Google ile açılan hesaplar kullanıcı adı almaz);
        # SQLite UNIQUE index'te birden fazla NULL'a izin verir, sorun oluşturmaz.
        connection.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username)")


init_database()


@dataclass(frozen=True)
class Entry:
    question: str
    answer: str
    terms: frozenset[str]


@dataclass(frozen=True)
class QuizItem:
    id: int
    category: str
    question: str
    answer: str
    choices: tuple[str, str, str, str]
    poster_url: str | None = None
    movie_title: str | None = None
    question_type: str = "fact"


def terms(text: str) -> frozenset[str]:
    """Small dependency-free lexical retriever for the initial local app."""
    found = set(re.findall(r"[a-z0-9']+", text.lower()))
    # The source questions are English while the interface is Turkish. These few
    # intent terms substantially improve initial retrieval without another model.
    turkish_intent = {
        "dizi": "series", "dizide": "series", "dizisi": "series",
        "film": "movie", "filmde": "movie", "filmi": "movie",
        "sarki": "song", "şarkı": "song", "muzik": "music", "müzik": "music",
        "oyuncu": "actor", "oynadı": "starred",
    }
    found.update(turkish_intent.get(word, word) for word in tuple(found))
    return frozenset(found)


def load_entries() -> list[Entry]:
    entries: list[Entry] = []
    with DATA_PATH.open(encoding="utf-8") as dataset:
        for line in dataset:
            messages = json.loads(line)["messages"]
            question, answer = messages[1]["content"].strip(), messages[2]["content"].strip()
            entries.append(Entry(question, answer, terms(question)))
    return entries


def load_quiz_items() -> list[QuizItem]:
    """Use only structurally valid multiple-choice rows from the source CSV files."""
    items: list[QuizItem] = []
    for category, filename in QUIZ_FILES.items():
        with Path(__file__).with_name(filename).open(encoding="utf-8", newline="") as dataset:
            for row in csv.DictReader(dataset):
                choices = tuple(row[key].strip() for key in "ABCD")
                answer = row["Correct"].strip()
                question = row["Questions"].strip()
                if question and answer in choices and len(set(choices)) == 4:
                    items.append(QuizItem(len(items), category, question, answer, choices))
    return items


def load_top_250_movies() -> list[dict[str, Any]]:
    """Load the single runtime film source built from the Top 250 catalogue."""
    if not TOP_250_PATH.exists():
        raise RuntimeError("imdb_top_250.json bulunamadı. Önce Top 250 veri setini oluşturun.")
    payload = json.loads(TOP_250_PATH.read_text(encoding="utf-8"))
    movies = payload.get("movies", [])
    if len(movies) != 250:
        raise RuntimeError(f"Top 250 kataloğu geçersiz: {len(movies)} kayıt bulundu.")
    return movies


# Eski IMDb/CSV dosyaları yalnızca geri dönüş yedeği olarak diskte tutulur.
# Çalışan uygulama bundan sonra film verisini TMDB'den alır.
TOP_250_MOVIES: list[dict[str, Any]] = []


def catalog_movie(record: dict[str, Any], request_text: str = "") -> dict[str, Any]:
    """Expose a stable, UI-friendly view without making a runtime API request."""
    return {
        "id": record["rank"],
        "rank": record["rank"],
        "title": record["title"],
        "original_title": record["title"],
        "year": str(record.get("year") or "—"),
        "genres": record.get("genres") or ["Film"],
        "moods": detect_moods(request_text, default=False),
        "note": record.get("overview") or record.get("tagline") or "Kısa açıklama bulunmuyor.",
        "overview": record.get("overview") or record.get("tagline") or "",
        "rating": record.get("imdb_rating"),
        "imdb_rating": record.get("imdb_rating"),
        "vote_count": record.get("vote_count", ""),
        "poster_url": record.get("poster_url"),
        "directors": record.get("directors") or [],
        "cast": record.get("cast") or [],
        "writers": record.get("writers") or [],
        "runtime": record.get("runtime", ""),
        "awards": record.get("awards", ""),
        "imdb_url": record.get("imdb_url", ""),
        "source": "IMDb Top 250",
        "source_key": "top250",
    }


def normalized_title(value: str) -> str:
    turkish_ascii = str.maketrans("çğıöşü", "cgiosu")
    return re.sub(r"[^a-z0-9]+", " ", value.lower().translate(turkish_ascii)).strip()


def title_is_mentioned(title: str, normalized_query: str) -> bool:
    """Match whole title phrases only; 'Ran' must not match Turkish 'karanlık'."""
    normalized = normalized_title(title)
    if not normalized:
        return False
    return re.search(rf"(?:^|\s){re.escape(normalized)}(?:$|\s)", normalized_query) is not None


def is_movie_fact_question(text: str) -> bool:
    """Keep the home mood compass focused on recommendations, not film lookup."""
    lowered = normalized_title(text)
    question_markers = (
        "yonetmeni kim", "yonetmen kim", "oyunculari kim", "kim oynuyor",
        "kadro kim", "imdb puani", "puani kac", "hangi tur", "turu ne",
        "ne anlatiyor", "konusu ne", "hikayesi ne", "hangi yil", "ne zaman cikti",
    )
    if any(marker in lowered for marker in question_markers):
        return True
    return any(
        re.search(pattern, lowered) is not None
        for pattern in (
            r"(?:yonetmen|oyuncu|kadro).{0,35}\bkim\b",
            r"imdb.{0,20}(?:puan|kac)",
            r"(?:tur|konu|hikaye).{0,24}(?:ne|hangi|anlatiyor)",
        )
    )


def catalogue_matches(query: str, limit: int = 8) -> list[dict[str, Any]]:
    """Retrieve Top 250 records locally before Qwen composes a reply.

    Exact title, director and actor mentions win decisively.  Otherwise a
    compact lexical score gives Qwen a useful, relevant slice of the catalogue
    without sending the whole 250-film JSON in every prompt.
    """
    normalized_query = normalized_title(query)
    query_words = set(normalized_query.split())
    high_score_words = ("en yuksek", "en iyi", "en basarili", "en yuksek puan", "top 250")
    if any(word in normalized_query for word in high_score_words):
        return [catalog_movie(movie, query) for movie in TOP_250_MOVIES[:limit]]

    scored: list[tuple[float, dict[str, Any]]] = []
    for movie in TOP_250_MOVIES:
        title = normalized_title(movie["title"])
        people = [normalized_title(name) for name in [*movie.get("directors", []), *movie.get("cast", [])]]
        metadata = " ".join([title, *people, *(normalized_title(genre) for genre in movie.get("genres", [])), normalized_title(movie.get("overview", ""))])
        score = 0.0
        if title_is_mentioned(title, normalized_query):
            score += 1000
        score += sum(450 for person in people if person and person in normalized_query)
        score += sum(8 for word in query_words if len(word) > 2 and word in metadata)
        score += float(movie.get("imdb_rating") or 0) / 100
        scored.append((score, movie))
    return [catalog_movie(movie, query) for _, movie in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]]


def build_top250_quiz_items() -> list[QuizItem]:
    """Generate varied factual Turkish quiz cards from the same Top 250 records."""
    director_pool = sorted({director for movie in TOP_250_MOVIES for director in movie.get("directors", [])})
    actor_pool = sorted({actor for movie in TOP_250_MOVIES for actor in movie.get("cast", [])})
    year_pool = sorted({str(movie["year"]) for movie in TOP_250_MOVIES if movie.get("year")})
    genre_pool = sorted({genre for movie in TOP_250_MOVIES for genre in movie.get("genres", [])})
    rating_pool = sorted({f"{float(movie['imdb_rating']):.1f} / 10" for movie in TOP_250_MOVIES if movie.get("imdb_rating")})
    quiz_items: list[QuizItem] = []
    rng = random.Random(250)

    def choices_for(answer: str, pool: list[str]) -> tuple[str, str, str, str]:
        alternatives = [value for value in pool if value != answer]
        choices = [answer, *rng.sample(alternatives, k=3)]
        rng.shuffle(choices)
        return tuple(choices)

    def add(category: str, question: str, answer: str, pool: list[str]) -> None:
        quiz_items.append(
            QuizItem(
                id=len(quiz_items),
                category=category,
                question=question,
                answer=answer,
                choices=choices_for(answer, pool),
            )
        )

    for movie in TOP_250_MOVIES:
        directors = movie.get("directors") or []
        if directors:
            add(
                "IMDb Top 250 · Yönetmen",
                f"{movie['title']} ({movie.get('year')}) filminin yönetmeni kimdir?",
                directors[0],
                director_pool,
            )
        cast = movie.get("cast") or []
        if cast:
            add(
                "IMDb Top 250 · Oyuncular",
                f"Aşağıdaki oyunculardan hangisi {movie['title']} filminde yer alır?",
                cast[0],
                actor_pool,
            )
        if movie.get("imdb_rating"):
            rating = f"{float(movie['imdb_rating']):.1f} / 10"
            add(
                "IMDb Top 250 · Puan",
                f"{movie['title']} filminin IMDb puanı hangisidir?",
                rating,
                rating_pool,
            )
        if movie.get("year"):
            year = str(movie["year"])
            add(
                "IMDb Top 250 · Film Bilgisi",
                f"{movie['title']} filmi hangi yıl gösterime girdi?",
                year,
                year_pool,
            )
        genres = movie.get("genres") or []
        if genres:
            add(
                "IMDb Top 250 · Tür",
                f"{movie['title']} filminin öne çıkan türlerinden biri hangisidir?",
                genres[0],
                genre_pool,
            )
    return quiz_items


# SineQuiz soruları artık TMDB'den anlık oluşturulur; CSV havuzu yüklenmez.
QUIZ_ITEMS: list[QuizItem] = []
QUIZ_BY_ID: dict[int, QuizItem] = {}

MOOD_KEYWORDS = {
    "relax": (
        "yorgun", "yoruld", "rahat", "sakin", "huzur", "stres", "stresli",
        "bunal", "daral", "sıkıld", "sikild", "yorgunum", "kafam dolu", "hafif", "dingin",
    ),
    "uplift": ("moral", "mutlu", "iyi his", "pozitif", "ilham", "umut", "keyif"),
    "funny": ("komedi", "gül", "neşeli", "eğlenceli", "komik", "kahkaha"),
    "emotional": ("duygusal", "hüzün", "hüzünlü", "ağla", "yalnız", "yalnızım", "içe dönük", "üzgün", "üzgünüm", "mutsuz", "keyifsiz", "moralim bozuk", "canım sıkkın", "canim sikkın"),
    "exciting": ("heyecan", "aksiyon", "gerilim", "adrenalin", "hızlı", "enerjik", "enerji", "hareketli"),
    "thoughtful": ("düşün", "gizem", "bilim", "felsefi", "zeka", "anlamlı", "derin"),
    "escape": ("kafa dağıt", "kafamı dağıt", "kafayı dağıt", "kaçış", "fantastik", "başka dünya", "büyü", "uzay", "hayal"),
}
MOOD_LABELS = {
    "relax": "rahatlatıcı", "uplift": "moral verici", "funny": "neşeli",
    "emotional": "duygusal", "exciting": "heyecanlı", "thoughtful": "düşündürücü", "escape": "kaçış",
}
GENRE_KEYWORDS = {
    "Komedi": ("komedi", "gül", "komik", "neşeli"),
    "Romantik": ("romantik", "aşk", "sevgi"),
    "Aksiyon": ("aksiyon", "hızlı", "adrenalin"),
    "Gerilim": ("gerilim", "heyecan"),
    "Gizem": ("gizem", "dedektif", "bulmaca"),
    "Bilim Kurgu": ("bilim kurgu", "uzay", "gelecek"),
    "Fantastik": ("fantastik", "büyü", "masal"),
    "Animasyon": ("animasyon", "çizgi"),
}
TMDB_GENRES = {
    "Aksiyon": 28, "Macera": 12, "Animasyon": 16, "Komedi": 35,
    "Suç": 80, "Belgesel": 99, "Drama": 18, "Aile": 10751,
    "Fantastik": 14, "Tarih": 36, "Korku": 27, "Müzik": 10402,
    "Gizem": 9648, "Romantik": 10749, "Bilim Kurgu": 878,
    "Gerilim": 53, "Savaş": 10752, "Western": 37,
}
TMDB_GENRE_NAMES = {genre_id: genre for genre, genre_id in TMDB_GENRES.items()}
# Film Ara filtre panelinde ilk açılışta gösterilen türler — kullanıcıların en
# sık arayacağı ~8 tür. Kalanı "+ N tür daha" ile açılır; ID'ler TMDB_GENRES'ten gelir.
CATALOG_FEATURED_GENRES = [
    "Aksiyon", "Komedi", "Drama", "Gerilim", "Romantik", "Bilim Kurgu", "Korku", "Animasyon",
]
GENRE_INTENTS = {
    "Aksiyon": ("aksiyon", "adrenalin", "hareketli", "hızlı", "kovalamaca", "savaş"),
    "Macera": ("macera", "keşif", "yolculuk"),
    "Animasyon": ("animasyon", "çizgi film", "pixar"),
    "Komedi": ("komedi", "komik", "gül", "hafif", "neşeli", "eğlenceli", "keyifli"),
    "Drama": ("dram", "duygusal", "ağlamak", "ağla", "hayat hikayesi"),
    "Aile": ("aile", "çocuk", "sıcak", "rahat"),
    "Fantastik": ("fantastik", "büyü", "masal", "başka dünya"),
    "Korku": ("korku", "korkmak", "korkutucu", "ürpertici", "dehşet", "cin", "hayalet"),
    "Gizem": ("gizem", "dedektif", "bulmaca", "sır"),
    "Romantik": ("romantik", "aşk", "sevgi", "ilişki"),
    "Bilim Kurgu": ("bilim kurgu", "uzay", "gelecek", "robot", "yapay zeka"),
    "Gerilim": ("gerilim", "heyecan", "gergin", "sürükleyici"),
}
MOOD_GENRE_HINTS = {
    "relax": ("Komedi", "Aile"),
    "uplift": ("Komedi", "Aile"),
    "funny": ("Komedi",),
    "emotional": ("Drama", "Romantik"),
    "exciting": ("Aksiyon", "Gerilim"),
    "thoughtful": ("Gizem", "Bilim Kurgu"),
    "escape": ("Fantastik", "Macera"),
}


def load_translation_cache() -> dict[str, dict[str, Any]]:
    try:
        with TRANSLATION_CACHE_PATH.open(encoding="utf-8") as cache:
            return json.load(cache)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


QUIZ_TRANSLATIONS = load_translation_cache()
_model: Any | None = None
_tokenizer: Any | None = None
_model_lock = threading.Lock()
_model_error: str | None = None
_model_loading = False
_embedder: Any | None = None
_embeddings: np.ndarray | None = None
_embedding_error: str | None = None
_embedding_loading = False
_embedding_lock = threading.Lock()
_generation_lock = threading.Lock()
_translation_cache_lock = threading.Lock()


def lexical_retrieve(query: str) -> list[tuple[float, Entry]]:
    query_terms = terms(query)
    if not query_terms:
        return []

    ranked: list[tuple[float, Entry]] = []
    for entry in ENTRIES:
        shared = len(query_terms & entry.terms)
        # Normalised overlap favours questions sharing distinctive terms.
        score = shared / (len(query_terms | entry.terms) ** 0.5)
        if score:
            ranked.append((score, entry))
    return sorted(ranked, key=lambda item: item[0], reverse=True)[:MAX_CANDIDATES]


def load_semantic_retriever() -> None:
    """Load a multilingual embedding model and cache the dataset vectors locally."""
    global _embedder, _embeddings, _embedding_error
    with _embedding_lock:
        if _embedder is not None and _embeddings is not None:
            return
        if _embedding_error:
            raise RuntimeError(_embedding_error)
        try:
            from sentence_transformers import SentenceTransformer

            # CPU keeps Apple unified memory available for Qwen's MLX inference.
            _embedder = SentenceTransformer(EMBEDDING_MODEL_ID, device="cpu")
            expected_shape = (len(ENTRIES), _embedder.get_embedding_dimension())
            if CACHE_PATH.exists():
                cached = np.load(CACHE_PATH)
                if cached.shape == expected_shape:
                    _embeddings = cached
                    return
            CACHE_PATH.parent.mkdir(exist_ok=True)
            _embeddings = _embedder.encode(
                [f"passage: {entry.question}" for entry in ENTRIES],
                normalize_embeddings=True,
                show_progress_bar=False,
                batch_size=32,
            ).astype(np.float32)
            np.save(CACHE_PATH, _embeddings)
        except Exception as error:
            _embedding_error = str(error)
            raise RuntimeError(_embedding_error) from error


def start_semantic_load() -> None:
    """Build embeddings in the background; lexical search stays responsive."""
    global _embedding_loading
    if _embedding_loading or _embeddings is not None or _embedding_error:
        return
    _embedding_loading = True

    def load_in_background() -> None:
        global _embedding_loading
        try:
            load_semantic_retriever()
        except RuntimeError:
            pass
        finally:
            _embedding_loading = False

    threading.Thread(target=load_in_background, daemon=True).start()


def retrieve(query: str) -> tuple[list[tuple[float, Entry]], str]:
    """Prefer semantic Turkish↔English retrieval, while retaining a useful fallback."""
    if _embedder is not None and _embeddings is not None:
        query_embedding = _embedder.encode(
            [f"query: {query}"], normalize_embeddings=True, show_progress_bar=False
        )[0]
        scores = _embeddings @ query_embedding
        indexes = np.argpartition(scores, -MAX_CANDIDATES)[-MAX_CANDIDATES:]
        indexes = indexes[np.argsort(scores[indexes])[::-1]]
        if float(scores[indexes[0]]) < SEMANTIC_CONFIDENCE_THRESHOLD:
            return [], "semantic"
        return [(float(scores[index]), ENTRIES[index]) for index in indexes], "semantic"

    start_semantic_load()
    return lexical_retrieve(query), "keyword"


def detect_moods(text: str, default: bool = True) -> list[str]:
    lowered = text.lower()
    detected = [mood for mood, words in MOOD_KEYWORDS.items() if any(word in lowered for word in words)]
    return detected or (["uplift", "relax"] if default else [])


CATALOGUE_GENRE_ALIASES = {"Dram": "Drama", "Bilim-Kurgu": "Bilim Kurgu"}
DARK_GENRES = {"Korku", "Gerilim", "Suç", "Savaş"}
LIGHT_TONE_MARKERS = (
    "ağır olmayan", "agir olmayan", "ağır olmasın", "agir olmasin", "hafif",
    "rahatlatıcı", "rahatlatici", "iyi hisset", "umut veren", "sıcak", "sicak",
    "kafa dağıt", "kafami dagit", "kafamı dağıt",
)
DISTRESS_MARKERS = (
    "bunal", "daral", "stres", "yoruld", "yorgun", "kafam dolu", "sıkıld", "sikild",
    "canım sıkkın", "canim sikkın", "sıkkın", "sikkin",
)
DARK_AVOIDANCE_MARKERS = (
    "karanlık olmayan", "karanlik olmayan", "karanlık olmasın", "karanlik olmasin",
    "karanlık olmasın", "karanlık istemiyorum", "karanlik istemiyorum",
)
COMPANION_MARKERS = (
    "annemle", "babamla", "ailemle", "aileyle", "çocuklarla", "cocuklarla",
)


def normalize_recommendation_intent(text: str) -> str:
    """Tolerate small Turkish typos for intent parsing without altering UI copy.

    This is deliberately vocabulary-based fuzzy matching, not a fixed typo
    replacement table: its candidate words are derived from the application's
    existing mood, genre, tone and negation language.
    """
    phrases = [
        *[word for words in MOOD_KEYWORDS.values() for word in words],
        *[word for words in GENRE_INTENTS.values() for word in words],
        *LIGHT_TONE_MARKERS, *DISTRESS_MARKERS, *DARK_AVOIDANCE_MARKERS,
        "istemiyorum", "olmasın", "olmasin", "hariç", "sevmiyorum", "olmadan",
        "saat", "saatten", "dakika", "uzun", "kısa", "kisa", *COMPANION_MARKERS,
        "izleyeceğim", "izleyecegim",
    ]
    vocabulary: dict[str, str] = {}
    for phrase in phrases:
        for word in re.findall(r"[a-zçğıöşü]+", phrase.lower()):
            normalized = normalized_title(word)
            if len(normalized) >= 4:
                vocabulary.setdefault(normalized, word)

    def correct_token(match: re.Match[str]) -> str:
        token = match.group(0)
        normalized = normalized_title(token)
        if len(normalized) < 4 or normalized in vocabulary:
            return vocabulary.get(normalized, token)
        candidate, score = max(
            ((candidate, SequenceMatcher(None, normalized, candidate).ratio()) for candidate in vocabulary),
            key=lambda item: item[1], default=("", 0.0),
        )
        # Short words need higher confidence so names and uncommon requests are
        # not aggressively rewritten; 1–2 character mistakes remain tolerant.
        threshold = .82 if len(normalized) <= 5 else .78
        if score >= threshold and abs(len(candidate) - len(normalized)) <= 2:
            return vocabulary[candidate]
        return token

    return re.sub(r"[a-zA-ZçğıöşüÇĞİÖŞÜ]+", correct_token, text.lower())


def recommendation_text_needs_clarification(text: str) -> bool:
    """Only stop on clearly unintelligible input; natural free-form asks go to Qwen."""
    words = re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ]+", text.lower())
    if not words:
        return True
    # A lone consonant-only token has no dependable Turkish semantic signal.
    # Do not treat ordinary shorthand or a multi-word sentence as low confidence.
    return len(words) == 1 and len(words[0]) >= 4 and not re.search(r"[aeıioöuü]", words[0])


def normalized_movie_genres(genres: list[str] | tuple[str, ...]) -> set[str]:
    """Use the same genre spelling for the static IMDb catalogue and TMDB."""
    return {CATALOGUE_GENRE_ALIASES.get(genre, genre) for genre in genres}


def respects_preference_exclusions(movie: dict[str, Any], preferences: dict[str, Any]) -> bool:
    return not (normalized_movie_genres(movie.get("genres") or []) & set(preferences["exclude_genres"]))


def rank_top250_movies(text: str, limit: int = 10) -> list[dict[str, Any]]:
    """Rank only local Top 250 records; no runtime TMDB discovery is used."""
    preferences = movie_request_preferences(text)
    primary_genres = set(preferences["genres"])
    # Keep the genre the visitor actually wrote ahead of helpful additions such
    # as Comedy/Family.  For example, "kafa dağıtmalık aşk filmi" must favour
    # a romance, not merely any light family film.
    lowered = text.lower()
    directly_requested_genres = {
        genre
        for genre, keywords in GENRE_INTENTS.items()
        if any(keyword in lowered for keyword in keywords)
        and genre in primary_genres
    }
    mood_genres: set[str] = set()
    excluded = set(preferences["exclude_genres"])
    for mood in detect_moods(text, default=False):
        mood_genres.update(MOOD_GENRE_HINTS.get(mood, ()))

    ranked: list[tuple[float, dict[str, Any]]] = []
    normalized_query = normalized_title(text)
    for record in TOP_250_MOVIES:
        genres = normalized_movie_genres(record.get("genres") or [])
        score = float(record.get("imdb_rating") or 0) / 100
        if primary_genres:
            # An explicit genre is a promise to the visitor. Mood hints can
            # refine it, but must never overpower it (e.g. romance → LOTR).
            score += len(genres & directly_requested_genres) * 110
            score += len(genres & (primary_genres - directly_requested_genres)) * 40
            score += len(genres & mood_genres) * 8
        else:
            score += len(genres & mood_genres) * 40
        score -= len(genres & excluded) * 100
        title = normalized_title(record["title"])
        if title_is_mentioned(title, normalized_query):
            score += 1000
        if preferences["year_gte"] and (record.get("year") or 0) < preferences["year_gte"]:
            score -= 80
        if preferences["year_lte"] and (record.get("year") or 9999) > preferences["year_lte"]:
            score -= 80
        ranked.append((score, record))
    return [catalog_movie(record, text) for _, record in sorted(ranked, key=lambda item: item[0], reverse=True)[:limit]]


def tmdb_genres_for(text: str) -> list[int]:
    """Turn Turkish free text into relevant TMDB genre filters."""
    lowered = text.lower()
    genres = [
        genre for genre, keywords in GENRE_INTENTS.items()
        if any(keyword in lowered for keyword in keywords)
    ]
    if not genres:
        for mood in detect_moods(text, default=False):
            genres.extend(MOOD_GENRE_HINTS.get(mood, ()))
    if not genres:
        genres.extend(infer_genres_with_qwen(text))
    # Preserve intent order while removing duplicates.
    return list(dict.fromkeys(TMDB_GENRES[genre] for genre in genres if genre in TMDB_GENRES))


def infer_genres_with_qwen(text: str) -> list[str]:
    """Use the local LLM only for free-form moods our explicit Turkish rules miss."""
    try:
        model, tokenizer = get_model()
        from mlx_lm import generate
        allowed = ", ".join(TMDB_GENRES)
        messages = [
            {
                "role": "system",
                "content": (
                    "Türkçe film öneri niyet sınıflandırıcısısın. Kullanıcı mesajını yalnızca şu "
                    f"türlerden bir veya ikisine eşle: {allowed}. Sadece JSON dizisi döndür."
                ),
            },
            {"role": "user", "content": text},
        ]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        with _generation_lock:
            output = generate(model, tokenizer, prompt=prompt, max_tokens=40, verbose=False).strip()
        json_text = output[output.find("[") : output.rfind("]") + 1]
        try:
            genres = json.loads(json_text)
            selected = [genre for genre in genres if genre in TMDB_GENRES]
        except json.JSONDecodeError:
            selected = [genre for genre in TMDB_GENRES if genre.lower() in output.lower()]
        return selected[:2]
    except (RuntimeError, ValueError, ModuleNotFoundError):
        return []


@lru_cache(maxsize=128)
def movie_request_preferences(text: str) -> dict[str, Any]:
    """Interpret a full Turkish sentence into safe, structured TMDB filters."""
    lowered = text.lower()
    explicit = [
        genre for genre, keywords in GENRE_INTENTS.items()
        if any(keyword in lowered for keyword in keywords)
    ]
    exclusion_markers = ("istemiyorum", "olmasın", "olmasin", "hariç", "sevmiyorum", "olmadan")
    explicit_exclusions = []
    for genre, keywords in GENRE_INTENTS.items():
        for keyword in keywords:
            exclusion_pattern = (
                rf"{re.escape(keyword)}(?:\s+(?:film|filmi|türü|tarzı))?\s*"
                rf"(?:{'|'.join(exclusion_markers)})"
            )
            if re.search(exclusion_pattern, lowered):
                explicit_exclusions.append(genre)
                break
    preferences: dict[str, Any] = {
        "genres": [genre for genre in explicit if genre not in explicit_exclusions],
        "exclude_genres": explicit_exclusions,
        "year_gte": None,
        "year_lte": None,
        "runtime_lte": None,
        "sort_by": "popularity.desc",
        "is_explicit": bool(explicit or explicit_exclusions),
    }

    # Simple date preferences are predictable and do not need a model call.
    short_decade_match = re.search(r"(?<!\d)([5-9]\d)['’]?(?:lardan|lerden|lar|ler)", lowered)
    decade_match = re.search(r"(?<!\d)(19\d{2}|20\d{2})['’]?(?:lardan|lerden|lar|ler)", lowered)
    if short_decade_match:
        decade = 1900 + int(short_decade_match.group(1))
        preferences["year_gte"], preferences["year_lte"] = decade, decade + 9
    elif decade_match:
        decade = int(decade_match.group(1))
        preferences["year_gte"], preferences["year_lte"] = decade, decade + 9
    elif year_match := re.search(r"(?<!\d)(19\d{2}|20\d{2})(?!\d)", lowered):
        preferences["year_gte"] = preferences["year_lte"] = int(year_match.group(1))
    elif any(marker in lowered for marker in ("modern", "çağdaş", "cagdas", "yeni dönem", "yeni donem")):
        preferences["year_gte"] = 2000
    elif any(marker in lowered for marker in ("yeni çıkan", "yeni cikan", "son yıllar", "son yillar", "güncel", "guncel")):
        preferences["year_gte"] = 2015
    elif any(marker in lowered for marker in ("klasik", "eski dönem", "eski donem", "nostaljik")):
        preferences["year_lte"] = 1999
    if preferences["year_gte"] or preferences["year_lte"]:
        preferences["is_explicit"] = True
    runtime_match = re.search(
        r"(?<!\d)(\d+(?:[.,]\d+)?)\s*saat(?:ten)?\s+uzun\s+(?:olmasın|olmasin|istemiyorum)",
        lowered,
    )
    if runtime_match:
        preferences["runtime_lte"] = int(float(runtime_match.group(1).replace(",", ".")) * 60)
        preferences["is_explicit"] = True
    if any(phrase in lowered for phrase in ("en iyi", "yüksek puan", "kaliteli", "imdb")):
        preferences["sort_by"] = "vote_average.desc"

    detected_moods = detect_moods(text, default=False)
    light_request = any(marker in lowered for marker in LIGHT_TONE_MARKERS)
    avoid_dark_request = any(marker in lowered for marker in DARK_AVOIDANCE_MARKERS)
    distress_request = any(marker in lowered for marker in DISTRESS_MARKERS)
    if light_request:
        preferences["genres"].extend(("Komedi", "Aile"))
        preferences["exclude_genres"].extend(DARK_GENRES)
        if any(marker in lowered for marker in ("ağır", "agir", "kafa dağıt", "kafamı dağıt", "kafami dagit")):
            preferences["exclude_genres"].append("Drama")
        preferences["is_explicit"] = True
    if avoid_dark_request:
        preferences["exclude_genres"].extend(DARK_GENRES)
        for mood in detected_moods:
            preferences["genres"].extend(MOOD_GENRE_HINTS.get(mood, ()))
        preferences["is_explicit"] = True
    # A distress statement is a preference too: when the visitor names no genre,
    # favor warm, easy choices and keep dark genres out of the first result set.
    if distress_request and not explicit:
        preferences["genres"].extend(("Komedi", "Aile"))
        preferences["exclude_genres"].extend(DARK_GENRES)
        preferences["is_explicit"] = True
    # "Annemle izleyeceğim" gibi eşlik eden kişiyi belirten kısa günlük
    # istekleri, tür söylenmemişse aile dostu sonuçlara yönlendir.
    if any(marker in lowered for marker in COMPANION_MARKERS) and not explicit:
        preferences["genres"].append("Aile")
        preferences["exclude_genres"].extend(("Korku", "Gerilim"))
        preferences["is_explicit"] = True
    # A romantic comedy should not unexpectedly surface a horror title.
    if {"Romantik", "Komedi"}.issubset(preferences["genres"]):
        preferences["exclude_genres"].extend(("Korku", "Savaş"))

    preferences["genres"] = list(dict.fromkeys(
        genre for genre in preferences["genres"] if genre in TMDB_GENRES and genre not in preferences["exclude_genres"]
    ))
    preferences["exclude_genres"] = list(dict.fromkeys(
        genre for genre in preferences["exclude_genres"] if genre in TMDB_GENRES
    ))

    # Clear genre/year requests are faster and more predictable without an LLM pass.
    # Qwen remains reserved for indirect, natural-language moods and ambiguous asks.
    if preferences["is_explicit"]:
        return preferences

    # Qwen adds nuance: exclusions and indirect moods in long, natural sentences.
    try:
        model, tokenizer = get_model()
        from mlx_lm import generate
        allowed = ", ".join(TMDB_GENRES)
        messages = [
            {
                "role": "system",
                "content": (
                    "Türkçe film öneri niyet ayrıştırıcısısın. Aşağıdaki film türlerinden seçim yap: "
                    f"{allowed}. Kullanıcının cümlesini JSON olarak dön: "
                    '{"genres":["..."],"exclude_genres":["..."]}. '
                    "Sadece bu iki anahtarı kullan; tür isimlerini aynen listeden seç. "
                    "“istemiyorum”, “olmasın”, “hariç” gibi olumsuzlukları exclude_genres alanına koy."
                ),
            },
            {"role": "user", "content": text},
        ]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        with _generation_lock:
            output = generate(model, tokenizer, prompt=prompt, max_tokens=70, verbose=False).strip()
        json_text = output[output.find("{") : output.rfind("}") + 1]
        parsed = json.loads(json_text)
        model_genres = [genre for genre in parsed.get("genres", []) if genre in TMDB_GENRES]
        model_exclusions = [genre for genre in parsed.get("exclude_genres", []) if genre in TMDB_GENRES]
        preferences["genres"] = list(dict.fromkeys(preferences["genres"] or model_genres))
        preferences["exclude_genres"] = list(dict.fromkeys(explicit_exclusions + model_exclusions))
    except (RuntimeError, ValueError, TypeError, json.JSONDecodeError, ModuleNotFoundError):
        # Direct Turkish terms remain a reliable no-model fallback.
        pass

    if not preferences["genres"]:
        for mood in detect_moods(text, default=False):
            preferences["genres"].extend(MOOD_GENRE_HINTS.get(mood, ()))
    if not preferences["genres"]:
        preferences["genres"] = infer_genres_with_qwen(text)
    preferences["genres"] = [
        genre for genre in dict.fromkeys(preferences["genres"])
        if genre in TMDB_GENRES and genre not in preferences["exclude_genres"]
    ]
    return preferences


def chat_movie_title(text: str) -> str | None:
    """Extract a title only when the visitor is clearly asking about one film."""
    patterns = (
        r"^\s*[\"“]?(.+?)[\"”]?\s+(?:ne anlatıyor|konusu ne(?:dir)?|hikâyesi ne(?:dir)?|hikayesi ne(?:dir)?|hakkında bilgi ver|hakkında ne biliyorsun|nasıl bir film)\??\s*$",
        r"^\s*[\"“]?(.+?)[\"”]?\s+(?:filmi|film)\s+(?:ne anlatıyor|konusu ne(?:dir)?|nasıl bir film)\??\s*$",
    )
    for pattern in patterns:
        match = re.match(pattern, text, flags=re.IGNORECASE)
        if not match:
            continue
        title = match.group(1).strip(" ?!.,:;\"“”")
        if 2 <= len(title) <= 80:
            return title
    return None


def tmdb_movie_from_result(result: dict[str, Any], request_text: str) -> dict[str, Any] | None:
    """Normalize a TMDB item once so search and discovery return the same shape."""
    title = result.get("title") or result.get("original_title")
    if not title:
        return None
    release_date = result.get("release_date") or ""
    genre_names = [TMDB_GENRE_NAMES.get(genre_id, "Film") for genre_id in result.get("genre_ids", [])]
    poster_path = result.get("poster_path")
    backdrop_path = result.get("backdrop_path")
    return {
        "id": result.get("id"),
        "title": title,
        "original_title": result.get("original_title") or title,
        "year": release_date[:4] or "—",
        "genres": genre_names or ["Film"],
        "moods": detect_moods(request_text),
        "note": result.get("overview") or "Bu film için Türkçe açıklama henüz bulunmuyor.",
        "rating": result.get("vote_average"),
        "poster_url": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None,
        "backdrop_url": f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None,
        "source": "TMDB · Güncel katalog",
        "source_key": "tmdb",
    }


def tmdb_title_search(title: str, request_text: str, limit: int = 3) -> list[dict[str, Any]]:
    """Find the film the visitor named before using broad mood discovery."""
    if not TMDB_API_KEY:
        return []
    params = {
        "api_key": TMDB_API_KEY,
        "language": "tr-TR",
        "region": "TR",
        "include_adult": "false",
        "query": title,
        "page": "1",
    }
    url = f"{TMDB_API_BASE}/search/movie?{urlencode(params)}"
    try:
        import certifi

        api_request = Request(url, headers={"Accept": "application/json", "User-Agent": "LumeFilmBot/1.0"})
        secure_context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(api_request, timeout=8, context=secure_context) as response:
            results = json.load(response).get("results", [])
    except Exception:
        return []

    movies = []
    for result in results:
        movie = tmdb_movie_from_result(result, request_text)
        if movie is not None:
            movies.append(movie)
        if len(movies) == limit:
            break
    return movies


@lru_cache(maxsize=64)
def tmdb_recommendations(text: str, limit: int = 8) -> list[dict[str, Any]]:
    """Fetch poster-rich, Turkish movie data for the explicitly live source mode."""
    if not TMDB_API_KEY:
        return []

    named_title = chat_movie_title(text)
    if named_title:
        named_movies = tmdb_title_search(named_title, text, limit)
        if named_movies:
            return named_movies

    preferences = movie_request_preferences(text)
    genre_ids = [TMDB_GENRES[genre] for genre in preferences["genres"]]
    excluded_genre_ids = [TMDB_GENRES[genre] for genre in preferences["exclude_genres"]]
    params = {
        "api_key": TMDB_API_KEY,
        "language": "tr-TR",
        "region": "TR",
        "include_adult": "false",
        "include_video": "false",
        "sort_by": preferences["sort_by"],
        "vote_count.gte": "80",
        "vote_average.gte": "6.5",
        "page": "1",
    }
    if genre_ids:
        # Comma means AND in TMDB discovery: a two-part mood stays specific.
        params["with_genres"] = ",".join(str(genre_id) for genre_id in genre_ids)
    if excluded_genre_ids:
        params["without_genres"] = ",".join(str(genre_id) for genre_id in excluded_genre_ids)
    if preferences["year_gte"]:
        params["primary_release_date.gte"] = f"{preferences['year_gte']}-01-01"
    if preferences["year_lte"]:
        params["primary_release_date.lte"] = f"{preferences['year_lte']}-12-31"
    if preferences["runtime_lte"]:
        params["with_runtime.lte"] = preferences["runtime_lte"]
    url = f"{TMDB_API_BASE}/discover/movie?{urlencode(params)}"
    try:
        import certifi

        request = Request(url, headers={"Accept": "application/json", "User-Agent": "LumeFilmBot/1.0"})
        secure_context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(request, timeout=8, context=secure_context) as response:
            results = json.load(response).get("results", [])
    except Exception:
        return []

    movies = []
    for result in results:
        movie = tmdb_movie_from_result(result, text)
        if movie is not None and respects_preference_exclusions(movie, preferences):
            movies.append(movie)
        if len(movies) == limit:
            break
    return movies


def choose_movies_with_qwen(message: str, candidates: list[dict[str, Any]], limit: int = 3) -> list[dict[str, Any]]:
    """Let Qwen choose among retrieved Top 250 records without inventing films."""
    if len(candidates) <= limit:
        return candidates
    try:
        model, tokenizer = get_model()
        from mlx_lm import generate

        compact_catalogue = "\n".join(
            f"{movie['id']} | {movie['title']} ({movie['year']}) | {', '.join(movie['genres'])} | "
            f"Puan: {movie.get('imdb_rating') or movie.get('rating') or 'bilinmiyor'} | Kaynak: {movie.get('source', 'Film kaydı')} | {movie['note'][:180]}"
            for movie in candidates
        )
        messages = [
            {
                "role": "system",
                "content": (
                    "Türkçe film seçki editörüsün. Kullanıcının isteğine yalnızca verilen filmlerden en uygun "
                    f"{limit} tanesini seç. Sadece şu JSON nesnesini döndür: {{\"ids\":[numara,...]}}. "
                    "Yeni film ya da numara uydurma."
                ),
            },
            {"role": "user", "content": f"İstek: {message}\n\nAdaylar:\n{compact_catalogue}"},
        ]
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
        with _generation_lock:
            output = generate(model, tokenizer, prompt=prompt, max_tokens=60, verbose=False).strip()
        json_text = output[output.find("{") : output.rfind("}") + 1]
        chosen_ids = json.loads(json_text).get("ids", [])
        by_id = {movie["id"]: movie for movie in candidates}
        selected: list[dict[str, Any]] = []
        for movie_id in chosen_ids:
            movie = by_id.get(movie_id)
            if movie is not None and movie not in selected:
                selected.append(movie)
        for candidate in candidates:
            if len(selected) == limit:
                break
            if candidate not in selected:
                selected.append(candidate)
        return selected[:limit]
    except (RuntimeError, ValueError, TypeError, json.JSONDecodeError, ModuleNotFoundError):
        return candidates[:limit]


def movie_candidates(text: str, limit: int = 3) -> list[dict[str, Any]]:
    preferences = movie_request_preferences(text)
    candidates = rank_top250_movies(text)
    if preferences["is_explicit"]:
        return candidates[:limit]
    return choose_movies_with_qwen(text, candidates, limit)


VALID_SOURCES = {"top250", "tmdb", "mixed"}


def source_recommendations(text: str, source: str, limit: int = 3) -> list[dict[str, Any]]:
    """Build an explicit source-aware selection for the visible recommendation UI."""
    preferences = movie_request_preferences(text)
    is_explicit = preferences["is_explicit"]
    if source == "top250":
        return movie_candidates(text, limit)
    if source == "tmdb":
        live_candidates = tmdb_recommendations(text, limit=8)
        if not live_candidates:
            raise RuntimeError("Güncel katalog şu anda yanıt vermiyor. IMDb Top 250 modunu deneyebilirsin.")
        return live_candidates[:limit] if is_explicit else choose_movies_with_qwen(text, live_candidates, limit)

    if limit == 1:
        candidates = [*rank_top250_movies(text, limit=6), *tmdb_recommendations(text, limit=6)]
        if not candidates:
            return movie_candidates(text, 1)
        return candidates[:1] if is_explicit else choose_movies_with_qwen(text, candidates, 1)

    # Romantik isteklerde güncel çeşitlilik daha faydalıdır: bir klasik + iki güncel.
    # Diğer isteklerde iki klasik + bir güncel denge korunur.
    classic_limit = 1 if "Romantik" in preferences["genres"] else max(1, limit - 1)
    live_limit = max(1, limit - classic_limit)
    classics = movie_candidates(text, classic_limit)
    live_candidates = tmdb_recommendations(text, limit=8)
    live = live_candidates[:live_limit] if is_explicit else choose_movies_with_qwen(text, live_candidates, live_limit)
    return [*classics, *live][:limit]


ZODIAC_PROMPTS = {
    "Koç": "enerjik cesur hızlı tempolu aksiyon macera filmi",
    "Boğa": "sıcak rahatlatıcı görsel olarak güzel dram romantik film",
    "İkizler": "akıllı eğlenceli sürprizli komedi gizem filmi",
    "Yengeç": "duygusal sıcak aile dostluk temalı film",
    "Aslan": "gösterişli ilham veren müzik macera filmi",
    "Başak": "incelikli düşündürücü gizem suç filmi",
    "Terazi": "zarif romantik estetik komedi filmi",
    "Akrep": "karanlık sürükleyici gerilim gizem filmi",
    "Yay": "özgür ruhlu yolculuk macera komedi filmi",
    "Oğlak": "azimli ilham veren biyografi dram filmi",
    "Kova": "özgün gelecekçi bilim kurgu bağımsız film",
    "Balık": "hayalperest duygusal fantastik romantik film",
}

# Köşe Yazıları: her giriş TMDB /discover/movie için hazır bir tarif taşır.
# Film adları hiçbir zaman burada tutulmaz; sadece tür/kalite/sıralama kuralları
# ve editoryal metinler sabittir, filmlerin kendisi her zaman TMDB'den gelir.
EDITORIAL_COLUMNS: list[dict[str, Any]] = [
    {
        "slug": "yorgun-aksam",
        "category": "MOD",
        "title": "Yorgun Bir Akşamda İzlemelik 7 Kafa Dağıtmalık Film",
        "subtitle": "Bugün ağır hikâyelerle uğraşmak istemeyenlere.",
        "intro": "Her akşam derin bir hikâyeye hazır olmuyoruz. Bu yedi seçki, zihnini yormadan güldüren ve iyi hissettiren, hafif ama itinayla seçilmiş filmlerden oluşuyor.",
        "genres": ["Komedi", "Aile", "Animasyon", "Macera"],
        "exclude_genres": ["Korku", "Savaş"],
        "vote_average_gte": 6.3,
        "vote_count_gte": 250,
        "sort_by": "popularity.desc",
        "why": [
            "Zihnini yormadan güldürür.",
            "Hafif tempoda başlayıp keyifle biter.",
            "Ağır hiçbir şey taşımadan iyi vakit geçirtir.",
            "Kafa dağıtmak için başka hiçbir şeye ihtiyaç bırakmaz.",
        ],
    },
    {
        "slug": "ilk-15-dakika",
        "category": "SÜRÜKLEYİCİ",
        "title": "İlk 15 Dakikada Seni İçine Çeken 7 Film",
        "subtitle": "“Biraz bakıp kapatırım” deyip jeneriğe kadar kalacağın filmler.",
        "intro": "Bazı filmler daha ilk sahnede sözünü tutar. Bu seçki, açılışıyla seni koltuğa çivileyip jeneriğe kadar bırakmayan yedi filmden oluşuyor.",
        "genres": ["Gerilim", "Gizem", "Aksiyon", "Macera", "Suç"],
        "exclude_genres": [],
        "vote_average_gte": 6.3,
        "vote_count_gte": 400,
        "sort_by": "popularity.desc",
        "why": [
            "Açılış sahnesinden itibaren bırakmıyor.",
            "Merakını ilk dakikada yakalayıp sonuna kadar taşıyor.",
            "Ekranı kapatmak için bir sebep bırakmıyor.",
            "Tempoyu hiç düşürmeden ilerliyor.",
        ],
    },
    {
        "slug": "gece-yarisi",
        "category": "GECE",
        "title": "Gece Yarısından Sonra Daha Güzel Hissettiren 7 Film",
        "subtitle": "Işıkları kapat, telefonu bırak. Bazı filmlerin saati gecedir.",
        "intro": "Gece geç saatlerde her film aynı hissi vermez. Bu yedi seçki, sessizlikte daha da güçlenen atmosferik hikâyelerden oluşuyor.",
        "genres": ["Gizem", "Drama", "Romantik", "Bilim Kurgu"],
        "exclude_genres": [],
        "vote_average_gte": 6.6,
        "vote_count_gte": 200,
        "sort_by": "vote_average.desc",
        "why": [
            "Sessizlikte daha da güçlü bir atmosfer kurar.",
            "Geç saatin sakinliğine yavaşça eşlik eder.",
            "Işıklar kapandığında asıl o zaman açılır.",
            "Gecenin sessizliğinde daha derin hissettirir.",
        ],
    },
    {
        "slug": "arkadaslarla-gece",
        "category": "ARKADAŞLARLA",
        "title": "Arkadaşlarla Film Gecesini Kurtaracak 7 Film",
        "subtitle": "Kimsenin “başka bir şey açalım” demeyeceği filmler.",
        "intro": "Grup halinde film seçmek başlı başına bir sınav. Bu yedi film, herkesi aynı anda ekrana kilitleyip tartışma çıkmasını önlüyor.",
        "genres": ["Komedi", "Aksiyon", "Macera", "Gizem"],
        "exclude_genres": [],
        "vote_average_gte": 6.5,
        "vote_count_gte": 600,
        "sort_by": "popularity.desc",
        "why": [
            "Herkesi aynı anda ekrana kilitler.",
            "Grup içinde tartışma çıkmasına izin vermez.",
            "Salonun ortak zevkine hitap eder.",
            "Kimse yarıda bırakmak istemez.",
        ],
    },
    {
        "slug": "klise-olmayan-ask",
        "category": "ROMANTİK",
        "title": "Romantik Film Sevmeyenlere 7 Aşk Filmi",
        "subtitle": "Aşk var ama klişe olmak zorunda değil.",
        "intro": "“Romantik filmleri sevmiyorum” diyenler için bile bu yedi film bir istisna olabilir. Aşk burada süsleme değil, hikâyenin kendisi.",
        "genres": ["Romantik"],
        "exclude_genres": [],
        "vote_average_gte": 6.8,
        "vote_count_gte": 300,
        "sort_by": "vote_average.desc",
        "why": [
            "Aşkı klişeye boğmadan anlatır.",
            "Duyguyu abartmadan, gerçek hissettirir.",
            "Romantizmi tek bir kalıba sıkıştırmaz.",
            "Aşkı hikâyenin süsü değil, omurgası yapar.",
        ],
    },
    {
        "slug": "ters-gidecek-his",
        "category": "GERİLİM",
        "title": "Bir Şeyler Ters Gidecek Hissi Veren 7 Film",
        "subtitle": "Daha hiçbir şey olmadı ama sen bir şeylerin yolunda olmadığını biliyorsun.",
        "intro": "Bazı filmler sana korku değil, sürekli bir tedirginlik hissi verir. Bu yedi seçki, o hissi en iyi taşıyan gerilim ve gizem filmlerinden oluşuyor.",
        "genres": ["Gerilim", "Gizem", "Suç"],
        "exclude_genres": ["Korku"],
        "vote_average_gte": 6.3,
        "vote_count_gte": 300,
        "sort_by": "popularity.desc",
        "why": [
            "Daha hiçbir şey olmadan seni tedirgin eder.",
            "Gerilimi çığlıkla değil sessizlikle kurar.",
            "Bir şeylerin ters gideceğini hissettirip bırakmaz.",
            "Atmosferiyle sürekli tetikte tutar.",
        ],
    },
    {
        "slug": "hayatini-toparlama",
        "category": "İYİ HİSSET",
        "title": "Hayatını Toparlama İsteği Veren 7 Film",
        "subtitle": "Jenerik aktığında küçük bir hayat krizi ve biraz motivasyon.",
        "intro": "Bazı filmler bittiğinde sadece hikâyeyi değil, kendi hayatını da gözden geçiriyorsun. Bu yedi seçki, yeni bir başlangıç hissi taşıyan filmlerden oluşuyor.",
        "genres": ["Drama", "Komedi", "Macera"],
        "exclude_genres": [],
        "vote_average_gte": 6.5,
        "vote_count_gte": 250,
        "sort_by": "vote_average.desc",
        "keyword_terms": ["coming of age", "self-discovery", "new beginning"],
        "why": [
            "Jenerik aktığında küçük bir özeleştiri bırakır.",
            "Yeni bir başlangıç hissini canlı tutar.",
            "Karakterin dönüşümü seninkini de tetikler.",
            "İzledikten sonra bir şeyler değiştirmek istersin.",
        ],
    },
    {
        "slug": "yagmurlu-pazar",
        "category": "PAZAR",
        "title": "Yağmurlu Bir Pazar Gününe Yakışan 7 Film",
        "subtitle": "Battaniye, kahve ve dışarı çıkmamak için iyi bir bahane.",
        "intro": "Yağmurlu bir pazar için gereken tek şey iyi bir bahane. Bu yedi seçki, dışarı çıkmamak için mükemmel bir sebep.",
        "genres": ["Drama", "Komedi", "Romantik", "Fantastik", "Animasyon"],
        "exclude_genres": ["Korku"],
        "vote_average_gte": 6.4,
        "vote_count_gte": 250,
        "sort_by": "popularity.desc",
        "why": [
            "Battaniyenin altından çıkmak istemezsin.",
            "Sıcak ve sakin bir atmosfer taşır.",
            "Dışarı çıkmamak için mükemmel bir bahane olur.",
            "Kahveni yudumlarken içini ısıtır.",
        ],
    },
    {
        "slug": "kesif-hazine",
        "category": "KEŞİF",
        "title": "“Ben Bunu Nasıl Daha Önce İzlemedim?” Dedirten 7 Film",
        "subtitle": "Çok konuşulmayan ama keşfedince başkasına anlatmak isteyeceğin filmler.",
        "intro": "En popüler filmler her zaman en iyisi değildir. Bu yedi seçki, gözden kaçmış ama keşfedilmeyi hak eden filmlerden oluşuyor.",
        "genres": [],
        "exclude_genres": [],
        "vote_average_gte": 7.2,
        "vote_count_gte": 500,
        "vote_count_lte": 6000,
        "sort_by": "vote_average.desc",
        "why": [
            "Kimsenin çok konuşmadığı ama hak ettiği bir seçim.",
            "Keşfedince başkasına anlatmak istersin.",
            "Gözden kaçmış ama unutulmayacak bir film.",
            "Herkesin bildiği değil, herkesin bilmesi gereken bir film.",
        ],
    },
]
EDITORIAL_COLUMNS_BY_SLUG = {column["slug"]: column for column in EDITORIAL_COLUMNS}


def discussion_fallback(message: str, movie: dict[str, Any]) -> str:
    """A grounded fallback when the small local model cannot form a coherent debate reply."""
    text = normalized_title(message)
    overview = re.sub(r"\s+", " ", str(movie.get("overview") or movie.get("note") or "")).strip()
    if len(overview) > 260:
        overview = overview[:257].rsplit(" ", 1)[0] + "…"
    evidence = f"TMDB özetinin verdiği çerçeve şu: {overview}" if overview else "TMDB kaydında ayrıntılı bir özet bulunmuyor."
    character_name = "Ana karakter"
    for item in movie.get("characters", []):
        candidate = str(item.get("character") or "").strip()
        normalized_candidate = normalized_title(candidate)
        parts = [part for part in normalized_candidate.split() if len(part) > 2]
        if candidate and normalized_candidate and (
            normalized_candidate in text or (len(parts) > 1 and all(part in text for part in parts))
        ):
            character_name = candidate
            break
    if any(term in text for term in ("final", "sonu", "sahne")):
        return (
            f"TMDB özetinde {movie['title']} filminin bu ayrıntısı yer almadığı için belirli bir sahneyi uydurarak yorumlamak istemem. "
            f"{evidence} Bu doğrulanmış çerçevede {character_name}, kararlarının sonuçlarıyla yüzleşen biri olarak okunabilir. "
            "Öte yandan aynı bölüm, karakterin koşullar tarafından yönlendirildiğini savunan daha bağışlayıcı bir yorumla da okunabilir."
        )
    if any(term in text for term in ("hakli", "haksiz", "dogru", "yanlis")):
        return (
            f"Bence {character_name} için tamamen haklı demek zor. "
            f"{evidence} {movie['title']} filminin {', '.join(movie['genres'][:2]).lower()} çerçevesi davranışlarını anlaşılır kılsa da anlaşılır olmak ahlaken doğru olmak anlamına gelmiyor. "
            "Öte yandan karakterin içinde bulunduğu baskının seçeneklerini daralttığı ve bu yüzden daha bağışlayıcı değerlendirilmesi gerektiği savunulabilir."
        )
    return (
        f"Bence {movie['title']} tek bir yoruma kapanmıyor. {evidence} "
        f"Bu nedenle {character_name}, hem seçimleri hem de sonuçları üzerinden tartışılabilir; filmin {', '.join(movie['genres'][:2]).lower()} yapısı karakteri koşullarıyla birlikte düşünmeyi destekliyor. "
        "Öte yandan daha sert bir okuma, koşullar ne olursa olsun karakterin seçimlerinin sorumluluğunu taşıması gerektiğini savunabilir."
    )


def discussion_reply_is_usable(reply: str) -> bool:
    normalized = re.sub(r"\s+", " ", reply).strip()
    if not 100 <= len(normalized) <= 1600:
        return False
    words = normalized_title(normalized).split()
    groups = [tuple(words[index:index + 4]) for index in range(max(0, len(words) - 3))]
    return len(groups) == len(set(groups))


def ask_movie_bot(
    message: str, choices: list[dict[str, Any]], history: list[dict[str, str]] | None = None, spoiler_ok: bool = False,
) -> str:
    """Constrained local-LLM reply with a small, evidence-aware discussion mode."""
    model, tokenizer = get_model()
    from mlx_lm import generate
    from mlx_lm.sample_utils import make_repetition_penalty, make_sampler

    compact_question = normalized_title(message)
    response_shape = ""
    if "yonetmen" in compact_question:
        response_shape = "Bu bir yönetmen sorusu: tek satırda yalnızca `Film adı — Yönetmen adı` biçimini kullan."
    elif "imdb" in compact_question or "puan" in compact_question:
        response_shape = "Bu bir puan sorusu: tek satırda yalnızca `Film adı — IMDb puanı: X/10` biçimini kullan."
    elif any(term in compact_question for term in ("oyuncu", "kadro", "cast")):
        response_shape = "Bu bir oyuncu sorusu: yalnızca ilk doğrudan eşleşen filmin 3-5 oyuncusunu tek satırda yaz."
    discussion_terms = (
        "sence", "yorum", "dusun", "karakter", "davranis", "final", "sonu", "sahne", "tema", "mesaj",
        "senaryo", "sinematografi", "oyunculuk", "hakli", "haksiz", "katiliyor", "katilmiyor",
    )
    is_discussion = any(term in compact_question for term in discussion_terms)
    discussion_instruction = ""
    if is_discussion:
        discussion_instruction = (
            " Bu bir tartışma sorusu; Wikipedia özeti gibi yıl, tür veya oyuncu listeleyerek BAŞLAMA. "
            "3-6 doğal cümleyle doğrudan kendi görüşünü belirterek başla (mesela 'Bence...', 'Bana kalırsa...', "
            "'... tarafı ilginç geliyor' gibi), sonra bu görüşü yalnızca verilen özet, karakter, tür ve yapım "
            "bilgilerinden somut gerekçelerle destekle. Kullanıcının fikrine otomatik katılma; makul bir karşı "
            "okumaya kısaca yer ver ve mümkünse kullanıcıya küçük bir soru sorarak bitir. Kayıtta olmayan sahne, "
            "replik, akrabalık, motivasyon veya final ayrıntısı üretme; bilgi yetmiyorsa bunu açıkça söyle. "
            "Gerçek bir arkadaşınla filmi tartışıyormuş gibi yaz; ansiklopedi girdisi gibi yazma.\n"
            "Örnek üslup (yalnızca ton için, konusunu kopyalama): 'Bence Michael'ın en çarpıcı tarafı ailesini "
            "korumak isterken zamanla korkuyla yönetmeye başlaması. Vito'nun gücü ilişkiler üzerinden kurmasına "
            "karşı Michael giderek yalnızlaşıyor. Sen bu değişimi zayıflık olarak mı okuyorsun?'"
        )
    spoiler_instruction = (
        " Spoiler modu açık: kullanıcı filmi izlemiş, finali, önemli ölümleri ve twist'leri özgürce konuşabilirsin."
        if spoiler_ok else
        " Spoiler modu kapalı: filmin finalini, kimin öldüğünü veya önemli twist'lerini açık etme; spoiler gerektiren "
        "bir soru gelirse bunu nazikçe belirt ve istersen spoiler modunu açabileceğini hatırlat."
    )

    catalog = "\n".join(
        f"- {movie['title']} ({movie['year']}) | Kaynak: {movie.get('source', 'film kaydı')} | "
        f"Puan: {movie.get('imdb_rating') or movie.get('rating') or 'bilinmiyor'} | Tür: {', '.join(movie['genres'])} | "
        f"Yönetmen: {', '.join(movie.get('directors', [])) or 'bilinmiyor'} | Oyuncular: {', '.join(movie.get('cast', [])[:5]) or 'bilinmiyor'} | "
        f"Senaryo: {', '.join(movie.get('writers', [])[:4]) or 'bilinmiyor'} | Süre: {movie.get('runtime') or 'bilinmiyor'} dakika | "
        f"Ana karakterler: {', '.join('{actor} ({character})'.format(**item) for item in movie.get('characters', [])[:6]) or 'bilinmiyor'} | "
        f"Slogan: {movie.get('tagline') or 'bilinmiyor'} | Ülkeler: {', '.join(movie.get('countries', [])[:3]) or 'bilinmiyor'} | "
        f"Anahtar kelimeler: {', '.join(movie.get('keywords', [])[:10]) or 'bilinmiyor'} | Özet: {movie['note']}"
        for movie in choices
    )
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                    "Sen Film Sitesi adlı Türkçe film sohbet asistanısın. Yalnızca aşağıdaki TMDB film "
                    "kayıtlarındaki bilgilere dayan; film adı, oyuncu, yönetmen, puan, olay veya tür uydurma. "
                    "Kullanıcının yalnızca sorduğu bilgiyi cevapla: örneğin yönetmen sorusuna yalnızca ilk "
                    "doğrudan eşleşen filmin yönetmenini tek cümleyle yaz; başka film, olay özeti veya öneri ekleme. "
                    "Film veya karakter yorumu istendiğinde açık bir görüş belirt; kullanıcının yorumuna otomatik "
                    "olarak katılma. Uygunsa nazikçe karşı çık ve ikinci bir yorum olasılığı sun. Özet ve karakter "
                    "bilgilerinde olmayan belirli sahneleri, replikleri veya final ayrıntılarını uydurma; bağlam yetersizse "
                    "bunu dürüstçe söyle. Bir öneri istediğinde en uygun 1-3 filmi seç ve kısa gerekçe yaz. Yanıtı doğal "
                    f"Türkçe tut; markdown ve 'katalog' kelimesini kullanma. {response_shape}{discussion_instruction}{spoiler_instruction}"
            ),
        },
    ]
    for item in (history or [])[-6:]:
        role = item.get("role")
        content = str(item.get("content") or "").strip()[:500]
        if role in {"user", "assistant"} and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": f"Kullanıcı mesajı: {message}\n\nDoğrulanmış TMDB film kaydı:\n{catalog}"})
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    max_tokens = 240 if is_discussion else 130
    if "yonetmen" in compact_question:
        max_tokens = 18
    elif "imdb" in compact_question or "puan" in compact_question:
        max_tokens = 24
    elif any(term in compact_question for term in ("oyuncu", "kadro", "cast")):
        max_tokens = 45
    with _generation_lock:
        output = generate(
            model, tokenizer, prompt=prompt, max_tokens=max_tokens, verbose=False,
            sampler=make_sampler(temp=0.55, top_p=0.9),
            logits_processors=[make_repetition_penalty(1.3)],
        ).strip()
    output = re.sub(r"\*\*|__|##+\s*", "", output).strip()
    if is_discussion:
        # A response hitting the token budget mid-sentence reads as broken;
        # trim back to the last complete sentence instead of cutting a word off.
        sentence_end = max(output.rfind(mark) for mark in (".", "!", "?", "…"))
        if 0 <= sentence_end < len(output) - 1 and sentence_end >= 80:
            output = output[: sentence_end + 1]
    if is_discussion and not discussion_reply_is_usable(output):
        return discussion_fallback(message, choices[0])
    return output


def recommendation_reply(message: str, choices: list[dict[str, Any]]) -> str:
    """Return a complete, factual chat reply from the TMDB records on screen."""
    primary = choices[0]
    lowered = message.lower()
    tone = "bu akşamki isteğine"
    if any(word in lowered for word in ("komik", "eğlenceli", "hafif", "rahat")):
        tone = "hafif ve keyifli bir akşam isteğine"
    elif any(word in lowered for word in ("korku", "gerilim", "korkmak", "ürpertici")):
        tone = "gerilimli bir akşam isteğine"
    elif any(word in lowered for word in ("romantik", "duygusal", "aşk", "aşık")):
        tone = "duygusal ve romantik bir akşam isteğine"
    elif any(word in lowered for word in ("aksiyon", "macera", "hareketli", "hızlı")):
        tone = "hareketli bir akşam isteğine"

    genres = " ve ".join(genre.lower() for genre in primary["genres"][:2])
    overview = primary["note"].strip()
    if len(overview) > 220:
        overview = f"{overview[:217].rsplit(' ', 1)[0]}…"
    reply = (
        f"{primary['title']} ile başlayabilirsin. {genres.capitalize()} tarafı {tone} iyi uyuyor; "
        f"hikâyesi de kısaca şöyle: {overview}"
    )
    if len(choices) > 1:
        alternative = choices[1]
        reply += f" Bir alternatif olarak {alternative['title']} da {', '.join(alternative['genres'][:2]).lower()} tonuyla listede duruyor."
    return reply


def get_model() -> tuple[Any, Any]:
    """Download/load Qwen only when the first search is submitted."""
    global _model, _tokenizer, _model_error
    with _model_lock:
        if _model is not None:
            return _model, _tokenizer
        if _model_error:
            raise RuntimeError(_model_error)
        try:
            from mlx_lm import load

            _model, _tokenizer = load(MODEL_ID)
            return _model, _tokenizer
        except Exception as error:  # Keep exact retrieval usable if MLX is unavailable.
            _model_error = str(error)
            raise RuntimeError(_model_error) from error


def start_model_load() -> None:
    """Warm the model in the background; searches remain available meanwhile."""
    global _model_loading
    if _model_loading or _model is not None or _model_error:
        return
    _model_loading = True

    def load_in_background() -> None:
        global _model_loading
        try:
            get_model()
        except RuntimeError:
            pass
        finally:
            _model_loading = False

    threading.Thread(target=load_in_background, daemon=True).start()


def ask_qwen(query: str, matches: list[tuple[float, Entry]]) -> str:
    model, tokenizer = get_model()
    from mlx_lm import generate

    references = "\n\n".join(
        f"Question: {entry.question}\nDataset answer: {entry.answer}"
        for _, entry in matches
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are an entertainment-trivia search assistant. Answer in Turkish, "
                "briefly. Use only the supplied dataset references. If none directly "
                "answers the user's request, say that there is no reliable match."
            ),
        },
        {
            "role": "user",
            "content": f"User search: {query}\n\nDataset references:\n{references}",
        },
    ]
    prompt = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
    )
    with _generation_lock:
        return generate(model, tokenizer, prompt=prompt, max_tokens=100, verbose=False).strip()


def translated_quiz_content(item: QuizItem) -> dict[str, Any]:
    """Translate a new quiz card once, preserving originals for answer checking."""
    if item.category.startswith("IMDb Top 250"):
        return {"question": item.question, "choices": list(item.choices), "version": 2}
    cache_key = str(item.id)
    with _translation_cache_lock:
        cached = QUIZ_TRANSLATIONS.get(cache_key)
    # Versioned entries prevent an old English fallback from becoming permanent.
    if cached and cached.get("version") == 2:
        return cached

    try:
        model, tokenizer = get_model()
        from mlx_lm import generate
    except (RuntimeError, ModuleNotFoundError):
        # The visual app remains usable before the optional local MLX runtime is installed.
        return {"question": item.question, "choices": list(item.choices), "version": 0}
    payload = json.dumps({"question": item.question, "choices": item.choices}, ensure_ascii=False)
    translated: dict[str, Any] | None = None
    for attempt in range(2):
        messages = [
            {
                "role": "system",
                "content": (
                    "You translate entertainment-trivia cards into natural Turkish. Every question "
                    "sentence must be Turkish; never return the original English wording unchanged. "
                    "Preserve only proper names, movie/TV/song/book titles, and quoted lyrics. "
                    "Return only valid JSON with exactly two keys: question (string) and choices "
                    "(an array of four strings in the original order)."
                ),
            },
            {
                "role": "user",
                "content": payload + ("\nThis is a retry: translate all explanatory wording to Turkish." if attempt else ""),
            },
        ]
        prompt = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True, enable_thinking=False
        )
        try:
            with _generation_lock:
                output = generate(model, tokenizer, prompt=prompt, max_tokens=500, verbose=False).strip()
            json_text = output[output.find("{") : output.rfind("}") + 1]
            candidate = json.loads(json_text)
            if not isinstance(candidate["question"], str) or not isinstance(candidate["choices"], list):
                raise ValueError("Unexpected translation shape")
            if len(candidate["choices"]) != 4 or not all(isinstance(choice, str) for choice in candidate["choices"]):
                raise ValueError("Unexpected number of translated choices")
            # If an English question is returned verbatim, make one stricter retry.
            if candidate["question"].strip() == item.question and attempt == 0:
                continue
            translated = {"question": candidate["question"], "choices": candidate["choices"], "version": 2}
            break
        except (RuntimeError, ValueError, KeyError, json.JSONDecodeError):
            continue

    if translated is None:
        # Keep the card usable, but do not cache this fallback: a later attempt may succeed.
        return {"question": item.question, "choices": list(item.choices), "version": 0}

    with _translation_cache_lock:
        QUIZ_TRANSLATIONS[cache_key] = translated
        TRANSLATION_CACHE_PATH.parent.mkdir(exist_ok=True)
        temporary_path = TRANSLATION_CACHE_PATH.with_suffix(".tmp")
        temporary_path.write_text(json.dumps(QUIZ_TRANSLATIONS, ensure_ascii=False), encoding="utf-8")
        temporary_path.replace(TRANSLATION_CACHE_PATH)
    return translated


# --- TMDB tek kaynak katmanı -------------------------------------------------
# Tüm görünür film bilgileri bu katmandan gelir. Önbellek, "güncel" kalırken
# her ziyaretçinin aynı isteği yeniden başlatmasını engeller.
_tmdb_cache: dict[str, tuple[float, Any]] = {}
_tmdb_cache_lock = threading.Lock()
_tmdb_quiz_by_id: dict[int, QuizItem] = {}
_tmdb_quiz_counter = 0


def tmdb_json(path: str, params: dict[str, Any] | None = None, ttl: int = 1800) -> dict[str, Any]:
    """Fetch one TMDB response with a small server-side TTL cache."""
    if not TMDB_API_KEY:
        raise RuntimeError("TMDB bağlantısı yapılandırılmamış.")
    query = {
        "api_key": TMDB_API_KEY,
        "language": "tr-TR",
        "region": "TR",
        **(params or {}),
    }
    cache_key = f"{path}?{urlencode(sorted(query.items()), doseq=True)}"
    now = time.monotonic()
    with _tmdb_cache_lock:
        cached = _tmdb_cache.get(cache_key)
        if cached and cached[0] > now:
            return cached[1]
    url = f"{TMDB_API_BASE}{path}?{urlencode(query, doseq=True)}"
    try:
        import certifi

        api_request = Request(url, headers={"Accept": "application/json", "User-Agent": "FilmSitesi/1.0"})
        secure_context = ssl.create_default_context(cafile=certifi.where())
        with urlopen(api_request, timeout=8, context=secure_context) as response:
            payload = json.load(response)
    except Exception as error:
        raise RuntimeError("TMDB güncel kataloğuna şu anda ulaşılamıyor.") from error
    with _tmdb_cache_lock:
        _tmdb_cache[cache_key] = (now + ttl, payload)
    return payload


def tmdb_movie(payload: dict[str, Any], request_text: str = "") -> dict[str, Any]:
    """Convert a TMDB list/detail response into the UI's one stable shape."""
    genre_payload = payload.get("genres") or []
    genres = [genre.get("name", "Film") for genre in genre_payload if isinstance(genre, dict)]
    if not genres:
        genres = [TMDB_GENRE_NAMES.get(genre_id, "Film") for genre_id in payload.get("genre_ids", [])]
    credits = payload.get("credits") or {}
    crew = credits.get("crew") or []
    cast = credits.get("cast") or []
    directors = [member.get("name") for member in crew if member.get("job") == "Director" and member.get("name")]
    writers = [
        member.get("name") for member in crew
        if member.get("job") in {"Writer", "Screenplay", "Story"} and member.get("name")
    ]
    keyword_payload = payload.get("keywords") or {}
    keywords = [
        item.get("name") for item in (keyword_payload.get("keywords") or keyword_payload.get("results") or [])
        if item.get("name")
    ]
    countries = [item.get("name") for item in payload.get("production_countries") or [] if item.get("name")]
    companies = [item.get("name") for item in payload.get("production_companies") or [] if item.get("name")]
    poster_path = payload.get("poster_path")
    backdrop_path = payload.get("backdrop_path")
    release_date = payload.get("release_date") or ""
    return {
        "id": payload.get("id"),
        "title": payload.get("title") or payload.get("original_title") or "Film",
        "original_title": payload.get("original_title") or payload.get("title") or "Film",
        "year": release_date[:4] or "—",
        "genres": genres or ["Film"],
        "moods": detect_moods(request_text),
        "note": payload.get("overview") or "Bu film için Türkçe açıklama henüz bulunmuyor.",
        "overview": payload.get("overview") or "",
        "rating": payload.get("vote_average"),
        "imdb_rating": payload.get("vote_average"),
        "poster_url": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None,
        "backdrop_url": f"https://image.tmdb.org/t/p/w1280{backdrop_path}" if backdrop_path else None,
        "directors": list(dict.fromkeys(directors)),
        "writers": list(dict.fromkeys(writers)),
        "cast": [member.get("name") for member in cast[:8] if member.get("name")],
        "characters": [
            {"actor": member.get("name"), "character": member.get("character")}
            for member in cast[:8]
            if member.get("name") and member.get("character")
        ],
        "runtime": payload.get("runtime") or "",
        "tagline": payload.get("tagline") or "",
        "original_language": payload.get("original_language") or "",
        "countries": countries,
        "production_companies": companies[:5],
        "keywords": keywords[:12],
        "source": "TMDB Güncel Katalog",
        "source_key": "tmdb",
    }


def tmdb_movie_detail(movie_id: int, request_text: str = "") -> dict[str, Any]:
    payload = tmdb_json(f"/movie/{movie_id}", {"append_to_response": "credits,keywords"}, ttl=86400)
    return tmdb_movie(payload, request_text)


def tmdb_movie_trailer_key(movie_id: int) -> str | None:
    """En uygun YouTube fragmanının video anahtarını döndürür, yoksa None.

    Öncelik: resmi YouTube fragmanı → herhangi bir YouTube fragmanı → yok.
    """
    try:
        payload = tmdb_json(f"/movie/{movie_id}/videos", ttl=21600)
    except RuntimeError:
        return None
    candidates = [
        video for video in payload.get("results") or []
        if video.get("site") == "YouTube" and video.get("type") == "Trailer" and video.get("key")
    ]
    if not candidates:
        return None
    official = next((video for video in candidates if video.get("official")), None)
    return (official or candidates[0])["key"]


def tmdb_watch_providers(movie_id: int) -> dict[str, Any]:
    """Return the Turkish watch availability in a small, UI-friendly shape."""
    payload = tmdb_json(f"/movie/{movie_id}/watch/providers", ttl=21600)
    country = (payload.get("results") or {}).get("TR") or {}

    def providers_for(*keys: str) -> list[dict[str, str]]:
        providers: list[dict[str, str]] = []
        seen: set[int] = set()
        for key in keys:
            for provider in country.get(key) or []:
                provider_id = int(provider.get("provider_id") or 0)
                if provider_id in seen:
                    continue
                seen.add(provider_id)
                logo_path = provider.get("logo_path")
                providers.append(
                    {
                        "name": provider.get("provider_name") or "Platform",
                        "logo_url": f"https://image.tmdb.org/t/p/w92{logo_path}" if logo_path else "",
                    }
                )
        return providers

    return {
        "region": "TR",
        "stream": providers_for("flatrate", "free", "ads"),
        "rent": providers_for("rent"),
        "buy": providers_for("buy"),
        "link": country.get("link") or "",
        "attribution": "JustWatch",
    }


def tmdb_discover_movies(text: str, limit: int = 8) -> list[dict[str, Any]]:
    preferences = movie_request_preferences(text)
    params: dict[str, Any] = {
        "include_adult": "false", "include_video": "false", "sort_by": preferences["sort_by"],
        "vote_count.gte": "80", "vote_average.gte": "6.2", "page": "1",
    }
    if preferences["genres"]:
        params["with_genres"] = ",".join(str(TMDB_GENRES[genre]) for genre in preferences["genres"])
    if preferences["exclude_genres"]:
        params["without_genres"] = ",".join(str(TMDB_GENRES[genre]) for genre in preferences["exclude_genres"])
    if preferences["year_gte"]:
        params["primary_release_date.gte"] = f"{preferences['year_gte']}-01-01"
    if preferences["year_lte"]:
        params["primary_release_date.lte"] = f"{preferences['year_lte']}-12-31"
    if preferences["runtime_lte"]:
        params["with_runtime.lte"] = preferences["runtime_lte"]
    results = tmdb_json("/discover/movie", params, ttl=1800).get("results", [])
    # TMDB treats comma-separated genres as an AND query. Natural-language moods
    # often describe alternatives, so retry them as OR before giving up.
    if not results and len(preferences["genres"]) > 1:
        relaxed_params = dict(params)
        relaxed_params["with_genres"] = "|".join(
            str(TMDB_GENRES[genre]) for genre in preferences["genres"]
        )
        results = tmdb_json("/discover/movie", relaxed_params, ttl=1800).get("results", [])
    # A mood sentence should never end in an empty screen. If TMDB has no exact
    # match, preserve quality/date filters but remove only the genre constraints.
    if not results:
        fallback_params = {
            key: value for key, value in params.items()
            if key not in {"with_genres", "without_genres"}
        }
        results = tmdb_json("/discover/movie", fallback_params, ttl=1800).get("results", [])
    movies = [tmdb_movie(item, text) for item in results]
    return [movie for movie in movies if respects_preference_exclusions(movie, preferences)][:limit]


CATALOG_PAGE_SIZE = 50
CATALOG_TMDB_PAGES_PER_PAGE = 3
CATALOG_SORT_MAP = {
    "popular": "popularity.desc",
    "rating": "vote_average.desc",
    "newest": "primary_release_date.desc",
    "oldest": "primary_release_date.asc",
}
CATALOG_RUNTIME_MAP: dict[str, tuple[int | None, int | None]] = {
    "short": (None, 90),
    "medium": (90, 120),
    "long": (120, None),
}

CATALOG_SEARCH_SCAN_PAGES = 3
CATALOG_SEARCH_DISCOVER_SCAN_PAGES = 6


def _tmdb_catalog_fetch(path: str, base_params: dict[str, Any], page: int) -> tuple[list[dict[str, Any]], int]:
    """Assemble one catalog page (~50 films) from several real TMDB pages.

    The UI paginates in blocks of CATALOG_PAGE_SIZE; each block maps to
    CATALOG_TMDB_PAGES_PER_PAGE consecutive TMDB pages so every numbered
    page shows a consistent amount of films instead of TMDB's default 20.
    """
    start_tmdb_page = (page - 1) * CATALOG_TMDB_PAGES_PER_PAGE + 1
    movies: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    total_tmdb_pages: int | None = None
    for offset in range(CATALOG_TMDB_PAGES_PER_PAGE):
        tmdb_page = start_tmdb_page + offset
        if tmdb_page > 500:
            break
        if total_tmdb_pages is not None and tmdb_page > total_tmdb_pages:
            break
        payload = tmdb_json(path, {**base_params, "page": str(tmdb_page)}, ttl=1800)
        total_tmdb_pages = payload.get("total_pages") or total_tmdb_pages or 1
        for result in payload.get("results", []):
            movie = tmdb_movie_from_result(result, "")
            if movie is None or movie["id"] in seen_ids:
                continue
            seen_ids.add(movie["id"])
            movies.append(movie)
    total_pages = max(1, -(-min(total_tmdb_pages or 1, 500) // CATALOG_TMDB_PAGES_PER_PAGE))
    return movies[:CATALOG_PAGE_SIZE], total_pages


def _tmdb_catalog_discover_params(filters: dict[str, Any]) -> dict[str, Any]:
    """Translate Film Ara's single filter state into TMDB discover parameters."""
    params: dict[str, Any] = {
        "include_adult": "false", "include_video": "false",
        "sort_by": filters.get("sort_by") or "popularity.desc",
        "vote_count.gte": str(filters.get("vote_count_gte") or 50),
    }
    if filters.get("genre_ids"):
        params["with_genres"] = ",".join(str(genre_id) for genre_id in filters["genre_ids"])
    if filters.get("year_from"):
        params["primary_release_date.gte"] = f"{filters['year_from']}-01-01"
    if filters.get("year_to"):
        params["primary_release_date.lte"] = f"{filters['year_to']}-12-31"
    if filters.get("vote_average_gte"):
        params["vote_average.gte"] = str(filters["vote_average_gte"])
    if filters.get("runtime_gte"):
        params["with_runtime.gte"] = str(filters["runtime_gte"])
    if filters.get("runtime_lte"):
        params["with_runtime.lte"] = str(filters["runtime_lte"])
    if filters.get("language"):
        params["with_original_language"] = filters["language"]
    if filters.get("provider_ids"):
        # A comma keeps multiple selected providers as an AND condition.
        params["with_watch_providers"] = ",".join(str(provider_id) for provider_id in filters["provider_ids"])
        params["watch_region"] = "TR"
        params["with_watch_monetization_types"] = "flatrate|free|ads"
    return params


def tmdb_catalog_discover(filters: dict[str, Any], page: int) -> tuple[list[dict[str, Any]], int]:
    """Browse the live TMDB catalogue with structured filters (Film Ara)."""
    params = _tmdb_catalog_discover_params(filters)
    return _tmdb_catalog_fetch("/discover/movie", params, page)


def _catalog_result_matches(result: dict[str, Any], filters: dict[str, Any]) -> bool:
    """Apply filters available on TMDB search results before any intersection."""
    result_genres = {str(value) for value in result.get("genre_ids") or []}
    if filters.get("genre_ids") and not set(filters["genre_ids"]).issubset(result_genres):
        return False
    release_year = str(result.get("release_date") or "")[:4]
    if filters.get("year_from") and (not release_year or release_year < str(filters["year_from"])):
        return False
    if filters.get("year_to") and (not release_year or release_year > str(filters["year_to"])):
        return False
    if filters.get("vote_average_gte") and float(result.get("vote_average") or 0) < float(filters["vote_average_gte"]):
        return False
    if filters.get("language") and result.get("original_language") != filters["language"]:
        return False
    if int(result.get("vote_count") or 0) < int(filters.get("vote_count_gte") or 0):
        return False
    return True


def _catalog_sort_results(results: list[dict[str, Any]], sort_by: str) -> list[dict[str, Any]]:
    reverse = not sort_by.endswith(".asc")
    if sort_by.startswith("vote_average"):
        key = lambda item: float(item.get("vote_average") or 0)
    elif sort_by.startswith("primary_release_date"):
        key = lambda item: item.get("release_date") or "0000-00-00"
    else:
        key = lambda item: float(item.get("popularity") or 0)
    return sorted(results, key=key, reverse=reverse)


def tmdb_catalog_search(query: str, filters: dict[str, Any], page: int) -> tuple[list[dict[str, Any]], int]:
    """Search titles and apply every active Film Ara condition with AND semantics.

    TMDB has no endpoint that combines a title query with discover filters. Search
    candidates are therefore intersected with a filtered discover result set when
    runtime or Turkish provider availability is requested. All underlying calls
    use ``tmdb_json``'s TTL cache; no per-card provider requests are made.
    """
    search_results: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    total_search_pages = 1
    for search_page in range(1, CATALOG_SEARCH_SCAN_PAGES + 1):
        if search_page > total_search_pages:
            break
        payload = tmdb_json(
            "/search/movie",
            {"include_adult": "false", "query": query, "page": str(search_page)},
            ttl=1800,
        )
        total_search_pages = min(int(payload.get("total_pages") or 1), 500)
        for result in payload.get("results") or []:
            movie_id = int(result.get("id") or 0)
            if not movie_id or movie_id in seen_ids or not _catalog_result_matches(result, filters):
                continue
            seen_ids.add(movie_id)
            search_results.append(result)

    if filters.get("runtime_gte") or filters.get("runtime_lte") or filters.get("provider_ids"):
        eligible_ids: set[int] = set()
        discover_params = _tmdb_catalog_discover_params(filters)
        total_discover_pages = 1
        for discover_page in range(1, CATALOG_SEARCH_DISCOVER_SCAN_PAGES + 1):
            if discover_page > total_discover_pages:
                break
            payload = tmdb_json(
                "/discover/movie",
                {**discover_params, "page": str(discover_page)},
                ttl=1800,
            )
            total_discover_pages = min(int(payload.get("total_pages") or 1), 500)
            eligible_ids.update(int(item.get("id") or 0) for item in payload.get("results") or [])
        search_results = [result for result in search_results if int(result.get("id") or 0) in eligible_ids]

    ordered = _catalog_sort_results(search_results, filters.get("sort_by") or "popularity.desc")
    start = (page - 1) * CATALOG_PAGE_SIZE
    movies = [movie for result in ordered[start:start + CATALOG_PAGE_SIZE] if (movie := tmdb_movie_from_result(result, ""))]
    total_pages = max(1, -(-len(ordered) // CATALOG_PAGE_SIZE))
    return movies, total_pages


def tmdb_catalog_watch_providers() -> list[dict[str, Any]]:
    """Return TMDB's current movie providers for Turkey, ordered for that region."""
    payload = tmdb_json("/watch/providers/movie", {"watch_region": "TR"}, ttl=86400)
    providers: list[dict[str, Any]] = []
    for provider in payload.get("results") or []:
        priorities = provider.get("display_priorities") or {}
        priority = priorities.get("TR", provider.get("display_priority"))
        provider_id = int(provider.get("provider_id") or 0)
        if not provider_id or priority is None:
            continue
        providers.append({
            "id": provider_id,
            "name": provider.get("provider_name") or "Platform",
            "priority": int(priority),
        })
    providers.sort(key=lambda item: (item["priority"], item["name"]))
    return [{"id": item["id"], "name": item["name"]} for item in providers[:24]]


_editorial_recent_ids: dict[int, float] = {}
_editorial_recent_lock = threading.Lock()
_EDITORIAL_RECENT_TTL = 3600


def _register_editorial_picks(movie_ids: list[int]) -> None:
    """Remember recently used movies so other columns prefer alternates."""
    now = time.monotonic()
    with _editorial_recent_lock:
        for stale_id in [mid for mid, expiry in _editorial_recent_ids.items() if expiry <= now]:
            del _editorial_recent_ids[stale_id]
        for movie_id in movie_ids:
            _editorial_recent_ids[movie_id] = now + _EDITORIAL_RECENT_TTL


def _recent_editorial_ids() -> set[int]:
    now = time.monotonic()
    with _editorial_recent_lock:
        return {mid for mid, expiry in _editorial_recent_ids.items() if expiry > now}


def tmdb_keyword_id(term: str) -> int | None:
    """Look up a TMDB keyword id for a discover with_keywords filter."""
    try:
        results = tmdb_json("/search/keyword", {"query": term}, ttl=86400).get("results", [])
    except RuntimeError:
        return None
    return int(results[0]["id"]) if results else None


def _editorial_discover_params(column: dict[str, Any]) -> dict[str, Any]:
    params: dict[str, Any] = {
        "include_adult": "false", "include_video": "false",
        "sort_by": column.get("sort_by", "popularity.desc"),
        "vote_average.gte": str(column.get("vote_average_gte", 6.0)),
        "vote_count.gte": str(column.get("vote_count_gte", 100)),
    }
    if column.get("vote_count_lte"):
        params["vote_count.lte"] = str(column["vote_count_lte"])
    if column.get("popularity_lte"):
        params["popularity.lte"] = str(column["popularity_lte"])
    genre_ids = [TMDB_GENRES[name] for name in column.get("genres", []) if name in TMDB_GENRES]
    if genre_ids:
        params["with_genres"] = "|".join(str(genre_id) for genre_id in genre_ids)
    exclude_ids = [TMDB_GENRES[name] for name in column.get("exclude_genres", []) if name in TMDB_GENRES]
    if exclude_ids:
        params["without_genres"] = ",".join(str(genre_id) for genre_id in exclude_ids)
    return params


def tmdb_editorial_card_previews(column: dict[str, Any], limit: int = 4) -> list[dict[str, Any]]:
    """Cheap top-N lookup for a column's hub-card art (no dedup side effects)."""
    params = {**_editorial_discover_params(column), "page": "1"}
    try:
        results = tmdb_json("/discover/movie", params, ttl=3600).get("results", [])
    except RuntimeError:
        return []
    return [tmdb_movie(item) for item in results[:limit]]


def tmdb_editorial_column_movies(column: dict[str, Any], limit: int = 7) -> list[dict[str, Any]]:
    """Build one column's 7-film list straight from TMDB /discover/movie."""
    params = _editorial_discover_params(column)
    keyword_ids = [kid for kid in (tmdb_keyword_id(term) for term in column.get("keyword_terms", [])) if kid]
    if keyword_ids:
        params["with_keywords"] = "|".join(str(kid) for kid in keyword_ids)

    candidates: list[dict[str, Any]] = []
    seen_ids: set[int] = set()
    for page in ("1", "2"):
        results = tmdb_json("/discover/movie", {**params, "page": page}, ttl=3600).get("results", [])
        for item in results:
            movie_id = int(item.get("id") or 0)
            if not movie_id or movie_id in seen_ids:
                continue
            seen_ids.add(movie_id)
            candidates.append(tmdb_movie(item))
        if len(candidates) >= limit * 3:
            break

    if len(candidates) < limit and keyword_ids:
        # Keyword filtresi çok daraltmış olabilir; onsuz bir sayfa daha dene.
        relaxed = {key: value for key, value in params.items() if key != "with_keywords"}
        for item in tmdb_json("/discover/movie", {**relaxed, "page": "1"}, ttl=3600).get("results", []):
            movie_id = int(item.get("id") or 0)
            if not movie_id or movie_id in seen_ids:
                continue
            seen_ids.add(movie_id)
            candidates.append(tmdb_movie(item))

    if not candidates:
        raise RuntimeError("Bu köşe yazısı için TMDB'den yeterli film bulunamadı.")

    recent = _recent_editorial_ids()
    picked: list[dict[str, Any]] = []
    picked_ids: set[int] = set()
    for movie in candidates:
        if len(picked) >= limit:
            break
        if movie["id"] in recent:
            continue
        picked.append(movie)
        picked_ids.add(movie["id"])
    if len(picked) < limit:
        # Yeterli taze alternatif yoksa, tekrar kullanılmış olsa da listeyi tamamla.
        for movie in candidates:
            if len(picked) >= limit:
                break
            if movie["id"] in picked_ids:
                continue
            picked.append(movie)
            picked_ids.add(movie["id"])

    _register_editorial_picks([movie["id"] for movie in picked])
    return picked


def tmdb_title_query(text: str) -> str:
    """Strip common Turkish question wording, leaving the film title for TMDB search."""
    cleaned = normalized_title(text)
    cleaned = re.sub(
        r"\b(filminin|filmi|film|yonetmeni|yonetmen|oyunculari|oyuncu|kadro|kim|nedir|ne|"
        r"anlatiyor|konusu|hikayesi|imdb|puani|puan|hangi|yil|cikis|hakkinda|bilgi|ver)\b",
        " ", cleaned,
    )
    return re.sub(r"\s+", " ", cleaned).strip()


def tmdb_top250_catalogue() -> list[dict[str, Any]]:
    """Build TMDB's current first 250 top-rated films from 13 cached pages."""
    movies: list[dict[str, Any]] = []
    seen: set[int] = set()
    for page in range(1, 14):
        payload = tmdb_json("/movie/top_rated", {"page": page}, ttl=21600)
        for item in payload.get("results", []):
            movie_id = int(item.get("id") or 0)
            if not movie_id or movie_id in seen:
                continue
            seen.add(movie_id)
            movie = tmdb_movie(item)
            movie["rank"] = len(movies) + 1
            movie["source"] = "TMDB Top 250"
            movies.append(movie)
            if len(movies) == 250:
                return movies
    return movies


def top250_title_score(query: str, movie: dict[str, Any]) -> float:
    """Prefer a title explicitly named in a natural-language discussion prompt."""
    text = normalized_title(query)
    cleaned = tmdb_title_query(query)
    candidates = {
        normalized_title(str(movie.get("title", ""))),
        normalized_title(str(movie.get("original_title", ""))),
    } - {""}
    best = 0.0
    for title in candidates:
        if title in text:
            best = max(best, 10.0 + min(len(title), 50) / 100)
        if cleaned and (cleaned == title or cleaned in title):
            best = max(best, 9.0)
        if cleaned:
            best = max(best, SequenceMatcher(None, cleaned, title).ratio())
        query_terms = set(cleaned.split())
        title_terms = set(title.split())
        if title_terms:
            best = max(best, len(query_terms & title_terms) / len(title_terms))
            words = cleaned.split()
            title_length = len(title.split())
            for width in {max(1, title_length - 1), title_length, title_length + 1}:
                for index in range(max(0, len(words) - width + 1)):
                    phrase = " ".join(words[index:index + width])
                    best = max(best, SequenceMatcher(None, phrase, title).ratio())
    return best


def top250_character_score(query: str, movie: dict[str, Any]) -> float:
    """Find a named character from TMDB's own localized synopsis.

    TMDB's movie search endpoint does not index character names.  The Top 250
    records already include each film's overview, however, so a specific
    two-word name such as "Andy Dufresne" can be resolved before we load the
    relevant film's cast details.
    """
    ignored = {
        "film", "filmi", "filmin", "hakkinda", "kimdir", "kim", "nedir",
        "yorum", "yorumlayalim", "dusunuyorsun", "sence", "karakter",
        "ile", "ve", "bu", "bir", "mi", "mı",
    }
    terms = [term for term in normalized_title(query).split() if len(term) > 2 and term not in ignored]
    if len(terms) < 2:
        return 0.0
    overview = normalized_title(str(movie.get("overview") or movie.get("note") or ""))
    if not overview:
        return 0.0
    for width in range(min(4, len(terms)), 1, -1):
        for index in range(len(terms) - width + 1):
            phrase = " ".join(terms[index:index + width])
            if re.search(rf"(?:^|\s){re.escape(phrase)}(?:$|\s)", overview):
                return 20.0 + width / 100
    return 0.0


@lru_cache(maxsize=1)
def top250_chat_support_records() -> dict[int, dict[str, Any]]:
    """Index the bundled 250 records only as aliases for live TMDB IDs.

    A support record can help resolve an actor, director, writer or alternate
    title, but a result is returned only when that TMDB ID is also present in
    the current live Top 250 catalogue. Visible facts still come from TMDB.
    """
    try:
        records = load_top_250_movies()
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError):
        return {}
    return {
        int(record["tmdb_id"]): record
        for record in records
        if record.get("tmdb_id")
    }


def top250_support_score(query: str, movie: dict[str, Any]) -> float:
    """Resolve people and alternate titles without guessing an unrelated film."""
    record = top250_chat_support_records().get(int(movie.get("id") or 0))
    if not record:
        return 0.0
    text = normalized_title(query)
    local_title = normalized_title(str(record.get("title") or ""))
    if local_title and re.search(rf"(?:^|\s){re.escape(local_title)}(?:$|\s)", text):
        return 12.0

    best = 0.0
    for field in ("directors", "writers", "cast"):
        for person in record.get(field) or []:
            normalized_person = normalized_title(str(person))
            if not normalized_person:
                continue
            if re.search(rf"(?:^|\s){re.escape(normalized_person)}(?:$|\s)", text):
                best = max(best, 8.0 + min(len(normalized_person), 40) / 100)
                continue
            surname = normalized_person.split()[-1]
            if len(surname) >= 5 and re.search(rf"(?:^|\s){re.escape(surname)}(?:$|\s)", text):
                best = max(best, 7.0 + min(len(surname), 20) / 100)
    return best


def context_movie_mentions_person(text: str, context_movie: dict[str, Any]) -> bool:
    """True when the message names a character, actor or director already in play.

    Prevents a coincidental title match elsewhere (e.g. a film literally
    titled "Michael") from stealing the conversation away from the movie
    the visitor is already discussing when they clearly mean its character.
    """
    try:
        detail = tmdb_movie_detail(int(context_movie["id"]))
    except (RuntimeError, KeyError, TypeError, ValueError):
        return False
    normalized_query = normalized_title(text)

    def mentioned(name: str) -> bool:
        normalized_name = normalized_title(name)
        if not normalized_name:
            return False
        if re.search(rf"(?:^|\s){re.escape(normalized_name)}(?:$|\s)", normalized_query):
            return True
        return any(
            len(part) >= 3 and re.search(rf"(?:^|\s){re.escape(part)}(?:$|\s)", normalized_query)
            for part in normalized_name.split()
        )

    for item in detail.get("characters", []):
        if mentioned(str(item.get("character") or "")) or mentioned(str(item.get("actor") or "")):
            return True
    return any(mentioned(str(director)) for director in detail.get("directors", []))


def looks_like_named_entity_question(query: str) -> bool:
    """Detect queries where returning a merely popular film would be misleading."""
    text = normalized_title(query)
    markers = ("kimdir", "kim", "karakter", "yorumlayalim", "yorum", "davranisi", "hakli", "haksiz")
    return any(marker in text for marker in markers)


def tmdb_top250_chat_candidates(text: str, limit: int = 3, context_movie_id: int | None = None) -> list[dict[str, Any]]:
    catalogue = tmdb_top250_catalogue()
    if not catalogue:
        return []
    scored: list[tuple[float, float, float, float, dict[str, Any]]] = []
    for movie in catalogue:
        title_score = top250_title_score(text, movie)
        character_score = top250_character_score(text, movie)
        support_score = top250_support_score(text, movie)
        scored.append((max(title_score, character_score, support_score), title_score, character_score, support_score, movie))
    scored.sort(key=lambda item: (item[0], float(item[4].get("rating") or 0)), reverse=True)
    best_score, best_title_score, best_character_score, best_support_score, _ = scored[0]
    context_basic = next((movie for movie in catalogue if movie.get("id") == context_movie_id), None)
    if context_basic:
        normalized_query = normalized_title(text)
        follow_up_markers = (
            "peki", "bu film", "filmde", "filmin", "onun", "oyuncu", "kadro", "yonetmen",
            "senarist", "yazar", "puan", "sure", "kac dakika", "hangi yil", "hangi tur",
            "konu", "hikaye", "karakter", "final", "sonu", "sahne", "tema", "mesaj",
            "neden", "nasil", "sence", "hakkinda", "kim",
        )
        recommendation_markers = ("oner", "tavsiye", "benzer film", "baska film", "alternatif")
        mentions_context_person = context_movie_mentions_person(text, context_basic)
        changes_movie = (
            best_title_score >= 0.86 or best_support_score >= 7.0 or best_character_score >= 20.0
        ) and not mentions_context_person
        is_follow_up = mentions_context_person or any(marker in normalized_query for marker in follow_up_markers)
        asks_recommendation = any(marker in normalized_query for marker in recommendation_markers)
        if asks_recommendation and not changes_movie:
            context_genres = set(context_basic.get("genres") or [])
            similar = sorted(
                (
                    movie for movie in catalogue
                    if movie.get("id") != context_basic.get("id") and context_genres.intersection(movie.get("genres") or [])
                ),
                key=lambda movie: (
                    len(context_genres.intersection(movie.get("genres") or [])),
                    float(movie.get("rating") or 0),
                ),
                reverse=True,
            )[:limit]
            detailed_similar: list[dict[str, Any]] = []
            for basic in similar:
                detail = tmdb_movie_detail(int(basic["id"]), text)
                detail["rank"] = basic.get("rank")
                detail["source"] = "TMDB Top 250"
                detailed_similar.append(detail)
            return detailed_similar
        if is_follow_up and not asks_recommendation and not changes_movie:
            context_detail = tmdb_movie_detail(int(context_basic["id"]), text)
            context_detail["rank"] = context_basic.get("rank")
            context_detail["source"] = "TMDB Top 250"
            return [context_detail]
    selected: list[dict[str, Any]] = []
    # A name/character question must resolve to an actual TMDB title or a
    # character phrase in that title's TMDB synopsis. Do not replace an
    # unresolved name with the catalogue's first, unrelated movie.
    if looks_like_named_entity_question(text) and best_score < 0.72:
        return []
    if best_title_score >= 0.86 or best_character_score >= 20.0:
        selected = [scored[0][4]]
    elif best_support_score >= 7.0:
        selected = [movie for _, _, _, support_score, movie in scored if support_score >= max(7.0, best_support_score - 0.35)][:limit]
    elif best_score >= 0.72:
        selected = [movie for score, _, _, _, movie in scored if score >= max(0.58, best_score - 0.18)][:limit]
    elif context_movie_id:
        selected = [movie for movie in catalogue if movie.get("id") == context_movie_id]
    else:
        # `movie_request_preferences` ends in a Qwen guess that always names
        # *some* genre, so it can't tell "aksiyon filmi öner" (open request)
        # apart from "Sharknado hakkında ne düşünüyorsun?" (a specific title
        # we don't recognize). Decide that here first, cheaply and without
        # the model: only a direct genre keyword counts as an open request.
        # (detect_moods() is deliberately not used here — its "thoughtful"
        # trigger word "düşün" also matches ordinary opinion phrasing like
        # "ne düşünüyorsun", which would defeat this check for exactly the
        # named-but-unrecognized-title messages it needs to catch.)
        # Anything else with no score at all is reported as not-found by the
        # caller instead of silently swapping in a popular unrelated film.
        lowered_text = text.lower()
        has_direct_genre_signal = any(
            keyword in lowered_text
            for keywords in GENRE_INTENTS.values()
            for keyword in keywords
        )
        if has_direct_genre_signal:
            preferences = movie_request_preferences(text)
            wanted_genres = set(preferences.get("genres") or [])
            selected = [movie for movie in catalogue if wanted_genres.intersection(movie.get("genres") or [])][:limit]
            selected = selected or catalogue[:limit]

    detailed: list[dict[str, Any]] = []
    for basic in selected[:limit]:
        detail = tmdb_movie_detail(int(basic["id"]), text)
        detail["rank"] = basic.get("rank")
        detail["source"] = "TMDB Top 250"
        detailed.append(detail)
    return detailed


def tmdb_recommendation_choices(text: str, limit: int = 3) -> list[dict[str, Any]]:
    candidates = tmdb_discover_movies(text, limit=10)
    if not candidates:
        raise RuntimeError("TMDB güncel kataloğunda bu isteğe uygun film bulunamadı.")
    preferences = movie_request_preferences(text)
    return candidates[:limit] if preferences["is_explicit"] else choose_movies_with_qwen(text, candidates, limit)


def tmdb_fact_reply(question: str, movie: dict[str, Any]) -> str | None:
    """Keep factual chat answers exact by rendering the retrieved TMDB record directly."""
    text = normalized_title(question)
    if "yonetmen" in text:
        return f"{movie['title']} filminin yönetmeni: {', '.join(movie['directors']) or 'TMDB kaydında belirtilmemiş'}"
    if any(term in text for term in ("oyuncu", "kadro", "cast", "kim oynuyor")):
        return f"{movie['title']} oyuncuları: {', '.join(movie['cast'][:5]) or 'TMDB kaydında belirtilmemiş'}"
    if "karakter" in text and any(term in text for term in ("kim", "hangileri", "say")):
        characters = [f"{item['character']} — {item['actor']}" for item in movie.get("characters", [])[:6]]
        return f"{movie['title']} ana karakterleri: {', '.join(characters) or 'TMDB kaydında belirtilmemiş'}"
    if "imdb" in text or "puan" in text:
        rating = movie.get("rating")
        return f"{movie['title']} TMDB puanı: {float(rating):.1f} / 10" if rating is not None else None
    if any(term in text for term in ("hangi yil", "ne zaman", "cikis")):
        return f"{movie['title']} gösterim yılı: {movie['year']}"
    if any(term in text for term in ("hangi tur", "turu ne", "tarzi")):
        return f"{movie['title']} türleri: {', '.join(movie['genres'])}"
    if any(term in text for term in ("suresi", "kac dakika", "ne kadar suruyor")):
        runtime = movie.get("runtime")
        return f"{movie['title']} filminin süresi: {runtime} dakika" if runtime else None
    if any(term in text for term in ("senarist", "senaryoyu kim", "kim yazdi", "yazari kim")):
        return f"{movie['title']} senaryosu: {', '.join(movie.get('writers', [])[:4]) or 'TMDB kaydında belirtilmemiş'}"
    if any(term in text for term in ("hangi ulke", "yapim ulkesi")):
        return f"{movie['title']} yapım ülkeleri: {', '.join(movie.get('countries', [])[:4]) or 'TMDB kaydında belirtilmemiş'}"
    if any(term in text for term in ("orijinal adi", "orijinal ismi")):
        return f"{movie['title']} filminin orijinal adı: {movie.get('original_title') or movie['title']}"
    if any(term in text for term in ("ne anlatiyor", "konusu", "hikayesi")):
        return movie["note"]
    if any(term in text for term in ("hakkinda bilgi", "bilgi ver", "kisaca anlat", "taniyalim")):
        director = ", ".join(movie.get("directors", [])[:2]) or "TMDB kaydında belirtilmemiş"
        runtime = f", {movie['runtime']} dakika" if movie.get("runtime") else ""
        rating = f", TMDB puanı {float(movie['rating']):.1f}/10" if movie.get("rating") is not None else ""
        return (
            f"{movie['title']} ({movie['year']}), {', '.join(movie['genres'])} türlerinde bir film; "
            f"yönetmeni {director}{runtime}{rating}. {movie['note']}"
        )
    return None


def tmdb_trending_movies(limit: int = 12, time_window: str = "week") -> list[dict[str, Any]]:
    window = "day" if time_window == "day" else "week"
    ttl = 900 if window == "day" else 1800
    results = tmdb_json(f"/trending/movie/{window}", {"include_adult": "false"}, ttl=ttl).get("results", [])
    return [tmdb_movie(item, "") for item in results[:limit]]


def tmdb_quiz_catalogue() -> list[dict[str, Any]]:
    """Build a varied, poster-ready live catalogue without storing TMDB content locally."""
    sources = (
        ("/trending/movie/week", {"include_adult": "false"}),
        ("/movie/popular", {"page": 1, "include_adult": "false"}),
        ("/movie/popular", {"page": 2, "include_adult": "false"}),
        ("/movie/top_rated", {"page": 1}),
        ("/movie/top_rated", {"page": 2}),
    )
    catalogue: list[dict[str, Any]] = []
    seen: set[int] = set()
    for path, params in sources:
        for payload in tmdb_json(path, params, ttl=1800).get("results", []):
            movie_id = int(payload.get("id") or 0)
            if not movie_id or movie_id in seen or not payload.get("title"):
                continue
            seen.add(movie_id)
            catalogue.append(tmdb_movie(payload))
    return catalogue


def tmdb_quiz_question() -> QuizItem:
    global _tmdb_quiz_counter
    catalogue = tmdb_quiz_catalogue()
    poster_catalogue = [movie for movie in catalogue if movie.get("poster_url")]
    if len(poster_catalogue) < 4:
        raise RuntimeError("SineQuiz için TMDB verisi alınamadı.")

    def make_choices(answer: str, pool: list[str]) -> list[str]:
        alternatives = list(dict.fromkeys(value for value in pool if value and value != answer))
        if len(alternatives) < 3:
            raise RuntimeError("SineQuiz için yeterli seçenek bulunamadı.")
        choices = [answer, *random.sample(alternatives, k=3)]
        random.shuffle(choices)
        return choices

    # Both round types need cast credits, so details (which include credits) are
    # fetched once and reused for the poster+actor round and the fact-template round.
    detail_basics = random.sample(catalogue, k=min(10, len(catalogue)))
    details = [tmdb_movie_detail(int(item["id"])) for item in detail_basics if item.get("id")]
    if not details:
        raise RuntimeError("SineQuiz için TMDB ayrıntıları alınamadı.")

    director_pool = sorted({name for item in details for name in item.get("directors", [])})
    actor_pool = sorted({name for item in details for name in item.get("cast", [])})
    genre_pool = sorted({genre for item in details for genre in item.get("genres", [])})
    year_pool = sorted({str(item["year"]) for item in details if item.get("year") != "—"})
    rating_pool = sorted({f"{float(item['rating']):.1f} / 10" for item in details if item.get("rating")})
    poster_actor_candidates = [item for item in details if item.get("poster_url") and item.get("cast")]

    movie: dict[str, Any] | None = None
    category = question = answer = ""
    choices: list[str] = []
    question_type = "fact"

    def try_poster_round() -> bool:
        nonlocal movie, category, question, answer, choices, question_type
        if not poster_actor_candidates or len(actor_pool) < 4:
            return False
        candidate = random.choice(poster_actor_candidates)
        try:
            picked = make_choices(candidate["cast"][0], actor_pool)
        except RuntimeError:
            return False
        movie, category, question, answer, choices, question_type = (
            candidate, "TMDB · Afişten Oyuncu", "Bu filmde hangi oyuncu rol alıyor?",
            candidate["cast"][0], picked, "poster",
        )
        return True

    # Poster rounds (afiş + oyuncu sorusu) are the main game mode.
    if random.random() < 0.65 and try_poster_round():
        pass
    else:
        movie = random.choice(details)
        templates: list[tuple[str, str, list[str], str]] = []
        if movie.get("directors") and len(director_pool) >= 4:
            templates.append(("TMDB · Yönetmen", f"{movie['title']} filminin yönetmeni kimdir?", director_pool, movie["directors"][0]))
        if movie.get("cast") and len(actor_pool) >= 4:
            templates.append(("TMDB · Oyuncular", f"Aşağıdaki oyunculardan hangisi {movie['title']} filminde yer alır?", actor_pool, movie["cast"][0]))
        if movie.get("genres") and len(genre_pool) >= 4:
            templates.append(("TMDB · Tür", f"{movie['title']} filminin öne çıkan türlerinden biri hangisidir?", genre_pool, movie["genres"][0]))
        if movie.get("year") != "—" and len(year_pool) >= 4:
            templates.append(("TMDB · Film Bilgisi", f"{movie['title']} filmi hangi yıl gösterime girdi?", year_pool, str(movie["year"])))
        if movie.get("rating") and len(rating_pool) >= 4:
            rating = f"{float(movie['rating']):.1f} / 10"
            templates.append(("TMDB · Puan", f"{movie['title']} filminin TMDB puanı hangisidir?", rating_pool, rating))
        if not templates:
            # A poster+actor round is always a useful fallback when a current film
            # has too little credit data for a factual multiple-choice question.
            if not try_poster_round():
                raise RuntimeError("SineQuiz için yeterli soru verisi bulunamadı.")
        else:
            category, question, pool, answer = random.choice(templates)
            choices = make_choices(answer, pool)
            question_type = "fact"

    _tmdb_quiz_counter += 1
    item = QuizItem(
        10_000_000 + _tmdb_quiz_counter, category, question, answer, tuple(choices),
        poster_url=movie.get("poster_url"), movie_title=movie.get("title"), question_type=question_type,
    )
    _tmdb_quiz_by_id[item.id] = item
    return item


# --- Kullanıcı hesapları ve kişisel film listeleri ---------------------------
AUTH_EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
AUTH_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,24}$")
AUTH_LIST_TABLES = {"favorites": "favorites", "watchlist": "watchlist"}


def user_record(user_id: int | None) -> sqlite3.Row | None:
    if not user_id:
        return None
    with database_connection() as connection:
        return connection.execute(
            "SELECT id, name, username, email, avatar_url, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()


def user_payload(user: sqlite3.Row) -> dict[str, Any]:
    with database_connection() as connection:
        favorite_count = connection.execute(
            "SELECT COUNT(*) FROM favorites WHERE user_id = ?", (user["id"],)
        ).fetchone()[0]
        watchlist_count = connection.execute(
            "SELECT COUNT(*) FROM watchlist WHERE user_id = ?", (user["id"],)
        ).fetchone()[0]
    return {
        "id": user["id"], "name": user["name"], "username": user["username"], "email": user["email"],
        "avatarUrl": user["avatar_url"], "favoriteCount": favorite_count, "watchlistCount": watchlist_count,
    }


def current_user_record() -> sqlite3.Row | None:
    return user_record(session.get("user_id"))


def ensure_csrf_token() -> str:
    if not session.get("csrf_token"):
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


def api_login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user = current_user_record()
        if user is None:
            session.clear()
            return jsonify({"error": "Bu işlem için giriş yapmalısın."}), 401
        supplied_token = request.headers.get("X-CSRF-Token", "")
        expected_token = session.get("csrf_token", "")
        if request.method != "GET" and (
            not supplied_token or not expected_token or not secrets.compare_digest(supplied_token, expected_token)
        ):
            return jsonify({"error": "Oturum doğrulanamadı. Sayfayı yenileyip tekrar dene."}), 403
        return view(user, *args, **kwargs)
    return wrapped


def safe_movie_payload(payload: Any) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    try:
        movie_id = int(payload.get("id"))
    except (TypeError, ValueError):
        return None
    title = str(payload.get("title") or "").strip()[:180]
    if movie_id <= 0 or not title:
        return None
    genres = payload.get("genres") if isinstance(payload.get("genres"), list) else []
    return {
        "id": movie_id,
        "title": title,
        "year": str(payload.get("year") or "—")[:12],
        "genres": [str(genre)[:60] for genre in genres[:8]],
        "rating": payload.get("rating") if isinstance(payload.get("rating"), (int, float)) else None,
        "poster_url": str(payload.get("poster_url") or "")[:500],
        "backdrop_url": str(payload.get("backdrop_url") or "")[:500],
        "overview": str(payload.get("overview") or payload.get("note") or "")[:3000],
        "source": str(payload.get("source") or "TMDB Güncel Katalog")[:80],
    }


def safe_next_path(value: str | None, fallback: str = "/") -> str:
    candidate = (value or "").strip()
    return candidate if candidate.startswith("/") and not candidate.startswith("//") else fallback


@app.context_processor
def inject_auth_user() -> dict[str, Any]:
    user = current_user_record()
    return {"current_user": user_payload(user) if user else None}


@app.get("/api/auth/availability")
def auth_availability():
    field = (request.args.get("field") or "").strip().lower()
    raw_value = (request.args.get("value") or "").strip()
    if field == "email":
        value = raw_value.lower()
        if not AUTH_EMAIL_PATTERN.fullmatch(value):
            return jsonify({"available": False, "message": "Geçerli bir e-posta adresi gir."})
        with database_connection() as connection:
            taken = connection.execute("SELECT 1 FROM users WHERE email = ?", (value,)).fetchone() is not None
        message = "Bu e-posta zaten kayıtlı." if taken else "Bu e-posta kullanılabilir."
        return jsonify({"available": not taken, "message": message})
    if field == "username":
        if not AUTH_USERNAME_PATTERN.fullmatch(raw_value):
            return jsonify({
                "available": False,
                "message": "3-24 karakter, yalnızca harf/rakam/alt çizgi kullanabilirsin.",
            })
        with database_connection() as connection:
            taken = connection.execute(
                "SELECT 1 FROM users WHERE username = ?", (raw_value,)
            ).fetchone() is not None
        message = "Bu kullanıcı adı zaten kullanılıyor." if taken else "Bu kullanıcı adı kullanılabilir."
        return jsonify({"available": not taken, "message": message})
    return jsonify({"error": "Geçersiz alan."}), 400


@app.post("/api/auth/register")
def register_user():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name") or "").strip()
    username = str(payload.get("username") or "").strip()
    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")
    password_confirm = str(payload.get("passwordConfirm") or "")
    if len(name) < 2 or len(name) > 80:
        return jsonify({"error": "Adını en az 2 karakter olarak gir."}), 400
    if not AUTH_USERNAME_PATTERN.fullmatch(username):
        return jsonify({
            "error": "Kullanıcı adı 3-24 karakter olmalı ve yalnızca harf, rakam, alt çizgi içerebilir.",
        }), 400
    if not AUTH_EMAIL_PATTERN.fullmatch(email):
        return jsonify({"error": "Geçerli bir e-posta adresi gir."}), 400
    if len(password) < 8:
        return jsonify({"error": "Şifren en az 8 karakter olmalı."}), 400
    if password != password_confirm:
        return jsonify({"error": "Şifreler eşleşmiyor."}), 400
    with database_connection() as connection:
        # Kullanıcıya anlaşılır bir hata verebilmek için önce kontrol ediyoruz;
        # UNIQUE index (idx_users_username, email UNIQUE) asıl güvenceyi sağlar,
        # aşağıdaki IntegrityError yakalayıcı bir yarış durumuna karşı yedektir.
        if connection.execute("SELECT 1 FROM users WHERE email = ?", (email,)).fetchone():
            return jsonify({"error": "Bu e-posta adresi zaten kayıtlı. Giriş yapmayı deneyin."}), 409
        if connection.execute("SELECT 1 FROM users WHERE username = ?", (username,)).fetchone():
            return jsonify({"error": "Bu kullanıcı adı zaten kullanılıyor. Başka bir kullanıcı adı deneyin."}), 409
        try:
            cursor = connection.execute(
                "INSERT INTO users (name, username, email, password_hash) VALUES (?, ?, ?, ?)",
                (name, username, email, generate_password_hash(password)),
            )
            user_id = int(cursor.lastrowid)
        except sqlite3.IntegrityError:
            return jsonify({"error": "Bu e-posta veya kullanıcı adı zaten kullanılıyor."}), 409
    session.clear()
    session.permanent = True
    session["user_id"] = user_id
    csrf_token = ensure_csrf_token()
    user = user_record(user_id)
    return jsonify({"user": user_payload(user), "csrfToken": csrf_token}), 201


@app.post("/api/auth/login")
def login_user():
    payload = request.get_json(silent=True) or {}
    email = str(payload.get("email") or "").strip().lower()
    password = str(payload.get("password") or "")
    with database_connection() as connection:
        user = connection.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "E-posta veya şifre hatalı."}), 401
    session.clear()
    session.permanent = True
    session["user_id"] = int(user["id"])
    csrf_token = ensure_csrf_token()
    return jsonify({"user": user_payload(user), "csrfToken": csrf_token})


@app.get("/api/auth/me")
def auth_me():
    user = current_user_record()
    if user is None:
        return jsonify({"user": None, "csrfToken": None})
    return jsonify({"user": user_payload(user), "csrfToken": ensure_csrf_token()})


@app.post("/api/auth/logout")
@api_login_required
def logout_user(_user: sqlite3.Row):
    session.clear()
    return jsonify({"ok": True})


# --- Google ile giriş: yetkilendirme kodu akışı (Authorization Code flow). ---
# Mevcut e-posta/şifre girişiyle aynı session + CSRF mekanizmasını kullanır;
# ayrı bir token sistemi kurulmaz.
def google_oauth_authorize_url(state: str, redirect_uri: str) -> str:
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "prompt": "select_account",
        "access_type": "online",
    }
    return f"{GOOGLE_AUTH_ENDPOINT}?{urlencode(params)}"


def google_oauth_exchange_code(code: str, redirect_uri: str) -> dict[str, Any]:
    data = urlencode({
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }).encode("utf-8")
    import certifi

    api_request = Request(GOOGLE_TOKEN_ENDPOINT, data=data, headers={"Accept": "application/json"})
    secure_context = ssl.create_default_context(cafile=certifi.where())
    with urlopen(api_request, timeout=8, context=secure_context) as response:
        return json.load(response)


def google_oauth_userinfo(access_token: str) -> dict[str, Any]:
    import certifi

    api_request = Request(
        GOOGLE_USERINFO_ENDPOINT,
        headers={"Accept": "application/json", "Authorization": f"Bearer {access_token}"},
    )
    secure_context = ssl.create_default_context(cafile=certifi.where())
    with urlopen(api_request, timeout=8, context=secure_context) as response:
        return json.load(response)


@app.get("/auth/google/login")
def google_oauth_login() -> Any:
    if not GOOGLE_OAUTH_ENABLED:
        return redirect(url_for("login_page"))
    next_path = safe_next_path(request.args.get("next"), url_for("index"))
    state = secrets.token_urlsafe(24)
    session["google_oauth_state"] = state
    session["google_oauth_next"] = next_path
    redirect_uri = url_for("google_oauth_callback", _external=True)
    return redirect(google_oauth_authorize_url(state, redirect_uri))


@app.get("/auth/google/callback")
def google_oauth_callback() -> Any:
    next_path = session.pop("google_oauth_next", None) or url_for("index")
    expected_state = session.pop("google_oauth_state", None)
    state = request.args.get("state")
    code = request.args.get("code")
    if (
        not GOOGLE_OAUTH_ENABLED or request.args.get("error") or not code or not state
        or not expected_state or not secrets.compare_digest(state, expected_state)
    ):
        return redirect(url_for("login_page", next=next_path, google_error="1"))
    try:
        redirect_uri = url_for("google_oauth_callback", _external=True)
        tokens = google_oauth_exchange_code(code, redirect_uri)
        profile = google_oauth_userinfo(tokens["access_token"])
    except Exception:
        return redirect(url_for("login_page", next=next_path, google_error="1"))

    google_id = str(profile.get("sub") or "")
    email = str(profile.get("email") or "").strip().lower()
    if not google_id or not email or not profile.get("email_verified"):
        return redirect(url_for("login_page", next=next_path, google_error="1"))
    name = (
        str(profile.get("name") or "").strip()
        or f"{profile.get('given_name', '')} {profile.get('family_name', '')}".strip()
        or email.split("@")[0]
    )
    avatar_url = str(profile.get("picture") or "")[:500] or None

    with database_connection() as connection:
        user_row = connection.execute("SELECT id FROM users WHERE google_id = ?", (google_id,)).fetchone()
        if user_row is None:
            # Aynı e-postayla normal kayıt olmuş bir hesap varsa ona bağlan;
            # duplicate hesap oluşturulmaz.
            user_row = connection.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            if user_row is not None:
                connection.execute(
                    "UPDATE users SET google_id = ?, avatar_url = COALESCE(avatar_url, ?) WHERE id = ?",
                    (google_id, avatar_url, user_row["id"]),
                )
            else:
                cursor = connection.execute(
                    "INSERT INTO users (name, email, password_hash, google_id, avatar_url) VALUES (?, ?, ?, ?, ?)",
                    (name[:80], email, generate_password_hash(secrets.token_urlsafe(32)), google_id, avatar_url),
                )
                user_row = connection.execute("SELECT id FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
        user_id = int(user_row["id"])

    session.clear()
    session.permanent = True
    session["user_id"] = user_id
    ensure_csrf_token()
    return redirect(next_path)


@app.get("/api/user/movies")
def user_movies():
    user = current_user_record()
    if user is None:
        return jsonify({"error": "Listelerini görmek için giriş yapmalısın."}), 401
    result: dict[str, list[dict[str, Any]]] = {"favorites": [], "watchlist": []}
    with database_connection() as connection:
        for list_name, table in AUTH_LIST_TABLES.items():
            rows = connection.execute(
                f"SELECT movie_json FROM {table} WHERE user_id = ? ORDER BY id DESC", (user["id"],)
            ).fetchall()
            for row in rows:
                try:
                    result[list_name].append(json.loads(row["movie_json"]))
                except (TypeError, json.JSONDecodeError):
                    continue
    return jsonify(result)


@app.post("/api/user/movies/<list_name>")
@api_login_required
def add_user_movie(user: sqlite3.Row, list_name: str):
    table = AUTH_LIST_TABLES.get(list_name)
    movie = safe_movie_payload((request.get_json(silent=True) or {}).get("movie"))
    if table is None or movie is None:
        return jsonify({"error": "Geçerli bir film listesi seç."}), 400
    with database_connection() as connection:
        connection.execute(
            f"INSERT INTO {table} (user_id, movie_id, movie_json) VALUES (?, ?, ?) "
            f"ON CONFLICT(user_id, movie_id) DO UPDATE SET movie_json = excluded.movie_json",
            (user["id"], movie["id"], json.dumps(movie, ensure_ascii=False)),
        )
    return jsonify({"movie": movie, "saved": True})


@app.delete("/api/user/movies/<list_name>/<int:movie_id>")
@api_login_required
def remove_user_movie(user: sqlite3.Row, list_name: str, movie_id: int):
    table = AUTH_LIST_TABLES.get(list_name)
    if table is None:
        return jsonify({"error": "Geçerli bir film listesi seç."}), 400
    with database_connection() as connection:
        connection.execute(f"DELETE FROM {table} WHERE user_id = ? AND movie_id = ?", (user["id"], movie_id))
    return jsonify({"saved": False})


@app.delete("/api/user/movies/<list_name>")
@api_login_required
def clear_user_movies(user: sqlite3.Row, list_name: str):
    table = AUTH_LIST_TABLES.get(list_name)
    if table is None:
        return jsonify({"error": "Geçerli bir film listesi seç."}), 400
    with database_connection() as connection:
        connection.execute(f"DELETE FROM {table} WHERE user_id = ?", (user["id"],))
    return jsonify({"ok": True})


# ===== Blog (Seyirci Yazıları): kullanıcıların izledikleri filmler hakkında =====
# ===== yazdığı kısa yazılar. Köşe Yazıları'ndan ayrı bir sistem — editoryal   =====
# ===== seçkiler yerine gerçek kullanıcı içeriği; sahiplik user_id ile kontrol edilir. =====
BLOG_TITLE_MAX_LEN = 160
BLOG_CONTENT_MAX_LEN = 8000
BLOG_EXCERPT_LEN = 220
BLOG_COMMENT_MAX_LEN = 1000
BLOG_READING_WPM = 200

BLOG_POST_TYPES = [
    "İnceleme", "Karakter Analizi", "Final Üzerine", "Eleştiri", "Teori", "Film Üzerine", "Diğer",
]


BLOG_TURKISH_MONTHS = [
    "Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran",
    "Temmuz", "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık",
]


def format_blog_date(value: str) -> str:
    try:
        parsed = datetime.strptime(value.split(".")[0], "%Y-%m-%d %H:%M:%S")
    except (ValueError, AttributeError, IndexError):
        return value
    return f"{parsed.day} {BLOG_TURKISH_MONTHS[parsed.month - 1]} {parsed.year}"


def blog_excerpt(content: str) -> str:
    flattened = " ".join(content.split())
    if len(flattened) <= BLOG_EXCERPT_LEN:
        return flattened
    cut = flattened[:BLOG_EXCERPT_LEN].rsplit(" ", 1)[0]
    return f"{cut}…"


def blog_reading_time(content: str) -> int:
    words = len(content.split())
    return max(1, round(words / BLOG_READING_WPM))


def blog_post_to_dict(
    row: sqlite3.Row, *, viewer_id: int | None = None, is_liked: bool = False, is_saved: bool = False,
    with_content: bool = False,
) -> dict[str, Any]:
    data = {
        "id": row["id"],
        "user_id": row["user_id"],
        "author_name": row["author_name"],
        "movie_id": row["movie_id"],
        "movie_title": row["movie_title"],
        "movie_poster": row["movie_poster"],
        "movie_backdrop": row["movie_backdrop"] or row["movie_poster"],
        "movie_year": row["movie_year"],
        "post_type": row["post_type"],
        "title": row["title"],
        "excerpt": blog_excerpt(row["content"]),
        "reading_time": blog_reading_time(row["content"]),
        "created_at": row["created_at"],
        "date_label": format_blog_date(row["created_at"]),
        "updated_at": row["updated_at"],
        "view_count": row["view_count"],
        "like_count": row["like_count"],
        "comment_count": row["comment_count"],
        "is_liked": is_liked,
        "is_saved": is_saved,
        "is_owner": bool(viewer_id) and viewer_id == row["user_id"],
    }
    if with_content:
        data["content"] = row["content"]
    return data


BLOG_POST_SELECT = (
    "SELECT blog_posts.*, users.name AS author_name, "
    "(SELECT COUNT(*) FROM blog_post_likes WHERE blog_post_likes.post_id = blog_posts.id) AS like_count, "
    "(SELECT COUNT(*) FROM blog_comments WHERE blog_comments.post_id = blog_posts.id) AS comment_count "
    "FROM blog_posts JOIN users ON users.id = blog_posts.user_id"
)


def blog_post_row(post_id: int) -> sqlite3.Row | None:
    with database_connection() as connection:
        return connection.execute(
            f"{BLOG_POST_SELECT} WHERE blog_posts.id = ?", (post_id,)
        ).fetchone()


def blog_post_viewer_flags(post_id: int, viewer_id: int | None) -> tuple[bool, bool]:
    if not viewer_id:
        return False, False
    with database_connection() as connection:
        liked = connection.execute(
            "SELECT 1 FROM blog_post_likes WHERE post_id = ? AND user_id = ?", (post_id, viewer_id)
        ).fetchone() is not None
        saved = connection.execute(
            "SELECT 1 FROM blog_post_saves WHERE post_id = ? AND user_id = ?", (post_id, viewer_id)
        ).fetchone() is not None
    return liked, saved


def validate_blog_payload(payload: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    movie = payload.get("movie") if isinstance(payload.get("movie"), dict) else {}
    try:
        movie_id = int(movie.get("id"))
    except (TypeError, ValueError):
        movie_id = 0
    movie_title = str(movie.get("title") or "").strip()[:180]
    if movie_id <= 0 or not movie_title:
        return None, "Bir film seçmelisin."
    post_type = str(payload.get("post_type") or "").strip()
    if post_type not in BLOG_POST_TYPES:
        return None, "Bir yazı türü seçmelisin."
    title = str(payload.get("title") or "").strip()
    if not title:
        return None, "Yazına bir başlık eklemelisin."
    if len(title) > BLOG_TITLE_MAX_LEN:
        return None, f"Başlık en fazla {BLOG_TITLE_MAX_LEN} karakter olabilir."
    content = str(payload.get("content") or "").strip()
    if not content:
        return None, "Yazı alanı boş bırakılamaz."
    if len(content) > BLOG_CONTENT_MAX_LEN:
        return None, f"Yazı en fazla {BLOG_CONTENT_MAX_LEN} karakter olabilir."
    return {
        "movie_id": movie_id,
        "movie_title": movie_title,
        "movie_poster": str(movie.get("poster_url") or "")[:500] or None,
        "movie_backdrop": str(movie.get("backdrop_url") or "")[:500] or None,
        "movie_year": str(movie.get("year") or "—")[:12],
        "post_type": post_type,
        "title": title,
        "content": content,
    }, None


BLOG_PAGE_SIZE = 8


def blog_post_matches_query(row: sqlite3.Row, query: str) -> bool:
    haystack = " ".join([row["title"], row["content"], row["movie_title"], row["author_name"]]).lower()
    return query in haystack


@app.get("/api/blog/posts")
def blog_posts_list():
    user = current_user_record()
    viewer_id = int(user["id"]) if user else None
    query = (request.args.get("q") or "").strip().lower()
    movie_id = request.args.get("movie_id", type=int)
    sort = request.args.get("sort") or "newest"
    page = max(1, request.args.get("page", 1, type=int))

    with database_connection() as connection:
        rows = connection.execute(f"{BLOG_POST_SELECT} ORDER BY blog_posts.created_at DESC").fetchall()
        liked_ids = {r["post_id"] for r in connection.execute(
            "SELECT post_id FROM blog_post_likes WHERE user_id = ?", (viewer_id,)
        )} if viewer_id else set()
        saved_ids = {r["post_id"] for r in connection.execute(
            "SELECT post_id FROM blog_post_saves WHERE user_id = ?", (viewer_id,)
        )} if viewer_id else set()

    movie_options: list[dict[str, Any]] = []
    seen_movies: set[int] = set()
    for row in rows:
        if row["movie_id"] not in seen_movies:
            seen_movies.add(row["movie_id"])
            movie_options.append({"id": row["movie_id"], "title": row["movie_title"]})
    movie_options.sort(key=lambda item: item["title"].lower())

    filtered = rows
    if movie_id:
        filtered = [row for row in filtered if row["movie_id"] == movie_id]
    if query:
        filtered = [row for row in filtered if blog_post_matches_query(row, query)]

    if sort == "most_read":
        filtered = sorted(filtered, key=lambda row: row["view_count"], reverse=True)
    elif sort == "most_discussed":
        filtered = sorted(filtered, key=lambda row: row["comment_count"], reverse=True)
    # "newest" (Tümü / Son Yazılar) zaten created_at DESC sırasıyla geldi.

    total = len(filtered)
    total_pages = max(1, -(-total // BLOG_PAGE_SIZE))
    page = min(page, total_pages)
    start = (page - 1) * BLOG_PAGE_SIZE
    page_rows = filtered[start:start + BLOG_PAGE_SIZE]

    return jsonify({
        "posts": [
            blog_post_to_dict(row, viewer_id=viewer_id, is_liked=row["id"] in liked_ids, is_saved=row["id"] in saved_ids)
            for row in page_rows
        ],
        "page": page,
        "total_pages": total_pages,
        "total": total,
        "movies": movie_options,
        "sort": sort,
        "post_types": BLOG_POST_TYPES,
    })


@app.get("/api/blog/posts/<int:post_id>")
def blog_post_detail(post_id: int):
    row = blog_post_row(post_id)
    if row is None:
        return jsonify({"error": "Yazı bulunamadı."}), 404
    user = current_user_record()
    viewer_id = int(user["id"]) if user else None
    is_liked, is_saved = blog_post_viewer_flags(post_id, viewer_id)
    return jsonify({
        "post": blog_post_to_dict(row, viewer_id=viewer_id, is_liked=is_liked, is_saved=is_saved, with_content=True),
    })


@app.post("/api/blog/posts")
@api_login_required
def blog_post_create(user: sqlite3.Row):
    payload = request.get_json(silent=True) or {}
    fields, error = validate_blog_payload(payload)
    if error:
        return jsonify({"error": error}), 400
    with database_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO blog_posts (user_id, movie_id, movie_title, movie_poster, movie_backdrop, movie_year, "
            "post_type, title, content) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                user["id"], fields["movie_id"], fields["movie_title"], fields["movie_poster"], fields["movie_backdrop"],
                fields["movie_year"], fields["post_type"], fields["title"], fields["content"],
            ),
        )
        post_id = int(cursor.lastrowid)
    row = blog_post_row(post_id)
    return jsonify({"post": blog_post_to_dict(row, viewer_id=int(user["id"]), with_content=True)}), 201


@app.put("/api/blog/posts/<int:post_id>")
@api_login_required
def blog_post_update(user: sqlite3.Row, post_id: int):
    row = blog_post_row(post_id)
    if row is None:
        return jsonify({"error": "Yazı bulunamadı."}), 404
    if row["user_id"] != user["id"]:
        return jsonify({"error": "Bu yazıyı düzenleme yetkin yok."}), 403
    payload = request.get_json(silent=True) or {}
    fields, error = validate_blog_payload(payload)
    if error:
        return jsonify({"error": error}), 400
    with database_connection() as connection:
        connection.execute(
            "UPDATE blog_posts SET movie_id = ?, movie_title = ?, movie_poster = ?, movie_backdrop = ?, movie_year = ?, "
            "post_type = ?, title = ?, content = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (
                fields["movie_id"], fields["movie_title"], fields["movie_poster"], fields["movie_backdrop"],
                fields["movie_year"], fields["post_type"], fields["title"], fields["content"], post_id,
            ),
        )
    row = blog_post_row(post_id)
    is_liked, is_saved = blog_post_viewer_flags(post_id, int(user["id"]))
    return jsonify({
        "post": blog_post_to_dict(row, viewer_id=int(user["id"]), is_liked=is_liked, is_saved=is_saved, with_content=True),
    })


@app.delete("/api/blog/posts/<int:post_id>")
@api_login_required
def blog_post_delete(user: sqlite3.Row, post_id: int):
    row = blog_post_row(post_id)
    if row is None:
        return jsonify({"error": "Yazı bulunamadı."}), 404
    if row["user_id"] != user["id"]:
        return jsonify({"error": "Bu yazıyı silme yetkin yok."}), 403
    with database_connection() as connection:
        connection.execute("DELETE FROM blog_posts WHERE id = ?", (post_id,))
    return jsonify({"ok": True})


@app.post("/api/blog/posts/<int:post_id>/like")
@api_login_required
def blog_post_like_toggle(user: sqlite3.Row, post_id: int):
    if blog_post_row(post_id) is None:
        return jsonify({"error": "Yazı bulunamadı."}), 404
    with database_connection() as connection:
        already_liked = connection.execute(
            "SELECT 1 FROM blog_post_likes WHERE post_id = ? AND user_id = ?", (post_id, user["id"])
        ).fetchone() is not None
        if already_liked:
            connection.execute("DELETE FROM blog_post_likes WHERE post_id = ? AND user_id = ?", (post_id, user["id"]))
        else:
            connection.execute("INSERT INTO blog_post_likes (post_id, user_id) VALUES (?, ?)", (post_id, user["id"]))
        like_count = connection.execute(
            "SELECT COUNT(*) FROM blog_post_likes WHERE post_id = ?", (post_id,)
        ).fetchone()[0]
    return jsonify({"liked": not already_liked, "like_count": like_count})


@app.post("/api/blog/posts/<int:post_id>/save")
@api_login_required
def blog_post_save_toggle(user: sqlite3.Row, post_id: int):
    if blog_post_row(post_id) is None:
        return jsonify({"error": "Yazı bulunamadı."}), 404
    with database_connection() as connection:
        already_saved = connection.execute(
            "SELECT 1 FROM blog_post_saves WHERE post_id = ? AND user_id = ?", (post_id, user["id"])
        ).fetchone() is not None
        if already_saved:
            connection.execute("DELETE FROM blog_post_saves WHERE post_id = ? AND user_id = ?", (post_id, user["id"]))
        else:
            connection.execute("INSERT INTO blog_post_saves (post_id, user_id) VALUES (?, ?)", (post_id, user["id"]))
    return jsonify({"saved": not already_saved})


def blog_comment_to_dict(row: sqlite3.Row, *, viewer_id: int | None = None) -> dict[str, Any]:
    return {
        "id": row["id"],
        "post_id": row["post_id"],
        "user_id": row["user_id"],
        "author_name": row["author_name"],
        "content": row["content"],
        "created_at": row["created_at"],
        "date_label": format_blog_date(row["created_at"]),
        "is_owner": bool(viewer_id) and viewer_id == row["user_id"],
    }


@app.get("/api/blog/posts/<int:post_id>/comments")
def blog_post_comments_list(post_id: int):
    user = current_user_record()
    viewer_id = int(user["id"]) if user else None
    with database_connection() as connection:
        rows = connection.execute(
            "SELECT blog_comments.*, users.name AS author_name FROM blog_comments "
            "JOIN users ON users.id = blog_comments.user_id WHERE blog_comments.post_id = ? "
            "ORDER BY blog_comments.created_at ASC",
            (post_id,),
        ).fetchall()
    return jsonify({"comments": [blog_comment_to_dict(row, viewer_id=viewer_id) for row in rows]})


@app.post("/api/blog/posts/<int:post_id>/comments")
@api_login_required
def blog_post_comment_create(user: sqlite3.Row, post_id: int):
    if blog_post_row(post_id) is None:
        return jsonify({"error": "Yazı bulunamadı."}), 404
    payload = request.get_json(silent=True) or {}
    content = str(payload.get("content") or "").strip()
    if not content:
        return jsonify({"error": "Yorum boş olamaz."}), 400
    if len(content) > BLOG_COMMENT_MAX_LEN:
        return jsonify({"error": f"Yorum en fazla {BLOG_COMMENT_MAX_LEN} karakter olabilir."}), 400
    with database_connection() as connection:
        cursor = connection.execute(
            "INSERT INTO blog_comments (post_id, user_id, content) VALUES (?, ?, ?)", (post_id, user["id"], content)
        )
        comment_row = connection.execute(
            "SELECT blog_comments.*, users.name AS author_name FROM blog_comments "
            "JOIN users ON users.id = blog_comments.user_id WHERE blog_comments.id = ?",
            (int(cursor.lastrowid),),
        ).fetchone()
    return jsonify({"comment": blog_comment_to_dict(comment_row, viewer_id=int(user["id"]))}), 201


@app.delete("/api/blog/comments/<int:comment_id>")
@api_login_required
def blog_comment_delete(user: sqlite3.Row, comment_id: int):
    with database_connection() as connection:
        row = connection.execute("SELECT * FROM blog_comments WHERE id = ?", (comment_id,)).fetchone()
        if row is None:
            return jsonify({"error": "Yorum bulunamadı."}), 404
        if row["user_id"] != user["id"]:
            return jsonify({"error": "Bu yorumu silme yetkin yok."}), 403
        connection.execute("DELETE FROM blog_comments WHERE id = ?", (comment_id,))
    return jsonify({"ok": True})


@app.get("/")
def index() -> str:
    return render_template("index.html", page="home", page_title="Film Sitesi")


@app.get("/film-sohbeti")
@app.get("/sohbet")
def chat_page() -> str:
    return render_template("index.html", page="chat", page_title="Filmler Hakkında Sohbet · Film Sitesi")


@app.get("/sinequiz")
def quiz_page_view() -> str:
    return render_template("index.html", page="quiz", page_title="SineQuiz · Film Sitesi")


@app.get("/kose-yazisi")
def column_page_view() -> str:
    return render_template(
        "index.html", page="column", page_title="Köşe Yazısı · Film Sitesi",
        editorial_columns=EDITORIAL_COLUMNS, initial_slug=None,
    )


@app.get("/kose-yazisi/<slug>")
def column_detail_view(slug: str) -> Any:
    if slug != "zodiac" and slug not in EDITORIAL_COLUMNS_BY_SLUG:
        return redirect(url_for("column_page_view"))
    column = EDITORIAL_COLUMNS_BY_SLUG.get(slug)
    title = f"{column['title']} · Köşe Yazısı · Film Sitesi" if column else "Burcuna Göre İzlemen Gereken Filmler · Köşe Yazısı · Film Sitesi"
    return render_template(
        "index.html", page="column", page_title=title,
        editorial_columns=EDITORIAL_COLUMNS, initial_slug=slug,
    )


@app.get("/film-ara")
def catalog_page_view() -> str:
    featured_names = [name for name in CATALOG_FEATURED_GENRES if name in TMDB_GENRES]
    featured_set = set(featured_names)
    remaining = sorted(
        (item for item in TMDB_GENRES.items() if item[0] not in featured_set),
        key=lambda item: item[0],
    )
    catalog_genres = [(name, TMDB_GENRES[name]) for name in featured_names] + remaining
    return render_template(
        "index.html", page="catalog", page_title="Film Ara · Film Sitesi",
        catalog_genres=catalog_genres, catalog_genres_featured_count=len(featured_names),
    )


@app.get("/yardim")
def help_page() -> str:
    return render_template("index.html", page="help", page_title="Yardım · Film Sitesi")


@app.get("/ayarlar")
def settings_page() -> str:
    return render_template("index.html", page="settings", page_title="Ayarlar · Film Sitesi")


@app.get("/giris")
def login_page() -> Any:
    next_path = safe_next_path(request.args.get("next"), url_for("index"))
    if current_user_record():
        return redirect(next_path if next_path != url_for("index") else url_for("profile_page"))
    return render_template(
        "index.html", page="login", page_title="Giriş Yap · Film Sitesi", auth_next=next_path,
        google_oauth_enabled=GOOGLE_OAUTH_ENABLED,
    )


@app.get("/uye-ol")
def register_page() -> Any:
    next_path = safe_next_path(request.args.get("next"), url_for("index"))
    if current_user_record():
        return redirect(next_path if next_path != url_for("index") else url_for("profile_page"))
    return render_template(
        "index.html", page="register", page_title="Üye Ol · Film Sitesi", auth_next=next_path,
        google_oauth_enabled=GOOGLE_OAUTH_ENABLED,
    )


@app.get("/profilim")
def profile_page() -> str:
    return render_template(
        "index.html", page="profile", page_title="Profilim · Film Sitesi",
        google_oauth_enabled=GOOGLE_OAUTH_ENABLED,
    )


@app.get("/favorilerim")
@app.get("/favoriler")
def favorites_page() -> str:
    return render_template("index.html", page="favorites", page_title="Favorilerim · Film Sitesi")


@app.get("/izleme-listem")
def watchlist_page() -> str:
    return render_template("index.html", page="watchlist", page_title="İzleme Listem · Film Sitesi")


@app.get("/blog")
def blog_page() -> str:
    return render_template("index.html", page="blog", page_title="Seyirci Yazıları · Film Sitesi")


@app.get("/blog/yeni")
def blog_editor_new_page() -> str:
    return render_template(
        "index.html", page="blog-editor", page_title="Yazı Yaz · Film Sitesi",
        editor_mode="create", editor_post=None, blog_post_types=BLOG_POST_TYPES,
    )


@app.get("/blog/<int:post_id>/duzenle")
def blog_editor_edit_page(post_id: int) -> Any:
    row = blog_post_row(post_id)
    if row is None:
        return redirect(url_for("blog_page"))
    user = current_user_record()
    if user is None:
        return render_template(
            "index.html", page="blog-editor", page_title="Yazını Düzenle · Film Sitesi",
            editor_mode="edit", editor_post=None, blog_post_types=BLOG_POST_TYPES,
        )
    if row["user_id"] != user["id"]:
        return redirect(url_for("blog_post_page", post_id=post_id))
    editor_post = blog_post_to_dict(row, viewer_id=int(user["id"]), with_content=True)
    return render_template(
        "index.html", page="blog-editor", page_title="Yazını Düzenle · Film Sitesi",
        editor_mode="edit", editor_post=editor_post, blog_post_types=BLOG_POST_TYPES,
    )


@app.get("/blog/<int:post_id>")
def blog_post_page(post_id: int) -> str:
    row = blog_post_row(post_id)
    if row is None:
        return render_template("index.html", page="blog-post", page_title="Yazı bulunamadı · Film Sitesi", post=None)
    with database_connection() as connection:
        connection.execute("UPDATE blog_posts SET view_count = view_count + 1 WHERE id = ?", (post_id,))
    row = blog_post_row(post_id)
    user = current_user_record()
    viewer_id = int(user["id"]) if user else None
    is_liked, is_saved = blog_post_viewer_flags(post_id, viewer_id)
    post = blog_post_to_dict(row, viewer_id=viewer_id, is_liked=is_liked, is_saved=is_saved, with_content=True)
    return render_template(
        "index.html", page="blog-post", page_title=f"{post['title']} · Seyirci Yazıları · Film Sitesi", post=post,
    )


@app.get("/api/health")
def health():
    return jsonify(
        {
            "catalogueMovies": "TMDB canlı katalog",
            "quizItems": "TMDB ile anlık üretiliyor",
            "translatedQuizItems": 0,
            "source": "TMDB",
            "model": MODEL_ID,
            "loaded": _model is not None,
            "loading": _model_loading,
            "error": _model_error,
            "semanticRag": {
                "model": EMBEDDING_MODEL_ID,
                "ready": _embeddings is not None,
                "building": _embedding_loading,
                "error": _embedding_error,
            },
        }
    )


@app.get("/api/chat/top250-search")
def chat_top250_search():
    """Minimal title lookup for the Film Sohbeti film picker (not a chat turn)."""
    query = normalized_title(request.args.get("q", ""))
    if len(query) < 2:
        return jsonify({"movies": []})
    try:
        catalogue = tmdb_top250_catalogue()
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503
    def title_variants(movie: dict[str, Any]) -> list[str]:
        return [normalized_title(str(movie.get(key, ""))) for key in ("title", "original_title")]

    matches = [movie for movie in catalogue if any(query in variant for variant in title_variants(movie))]
    matches.sort(key=lambda movie: (not any(variant.startswith(query) for variant in title_variants(movie)), movie.get("rank", 999)))
    return jsonify({
        "movies": [
            {"id": movie["id"], "title": movie["title"], "year": movie["year"], "directors": movie.get("directors", [])}
            for movie in matches[:8]
        ]
    })


@app.post("/api/search")
def search():
    payload = request.get_json(silent=True) or {}
    query = str(payload.get("query", "")).strip()
    if len(query) < 2:
        return jsonify({"error": "Lütfen en az iki karakter yazın."}), 400
    context_movie_id = payload.get("movieId")
    try:
        context_movie_id = int(context_movie_id) if context_movie_id else None
    except (TypeError, ValueError):
        context_movie_id = None
    raw_history = payload.get("history") if isinstance(payload.get("history"), list) else []
    chat_history = [
        {"role": item.get("role"), "content": str(item.get("content") or "")}
        for item in raw_history[-6:]
        if isinstance(item, dict) and item.get("role") in {"user", "assistant"}
    ]
    spoiler_ok = bool(payload.get("spoiler"))
    try:
        matches = tmdb_top250_chat_candidates(query, limit=3, context_movie_id=context_movie_id)
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503
    if not matches:
        return jsonify({
            "error": "Şimdilik Film Sohbeti bölümünde TMDb Top 250 filmleriyle çalışıyorum. Yukarıdan bir film seçebilir ya da adını yazabilirsin."
        }), 404
    answer = tmdb_fact_reply(query, matches[0])
    if answer is None:
        try:
            answer = ask_movie_bot(query, matches, chat_history, spoiler_ok=spoiler_ok)
        except RuntimeError:
            # Yerel sohbet modeli kullanılamadığında bile TMDB kaydına dayalı
            # sohbeti kesintisiz sürdür. Bu, özellikle model ilk kez yüklenirken
            # kullanıcıya 503 hatası gösterilmesini engeller.
            answer = discussion_fallback(query, matches[0])

    return jsonify(
        {
            "answer": answer,
            "generated": True,
            "mode": "qwen-source-aware",
            "source": "tmdb-top250",
            "leadMovie": matches[0] if matches else None,
            "matches": matches[:3],
        }
    )


@app.get("/api/quiz")
def quiz_question():
    try:
        item = tmdb_quiz_question()
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503
    return jsonify({
        "id": item.id, "category": item.category, "question": item.question,
        "choices": list(item.choices), "displayChoices": list(item.choices),
        "posterUrl": item.poster_url, "movieTitle": item.movie_title, "questionType": item.question_type,
    })


@app.post("/api/quiz/check")
def check_quiz_answer():
    payload = request.get_json(silent=True) or {}
    item = _tmdb_quiz_by_id.get(payload.get("id"))
    if item is None:
        return jsonify({"error": "Soru bulunamadı. Lütfen yeni bir soru açın."}), 404
    selected = str(payload.get("choice", "")).strip()
    return jsonify(
        {
            "correct": selected == item.answer,
            "answer": item.answer,
            "answerDisplay": item.answer,
            "questionType": item.question_type,
        }
    )


@app.post("/api/recommend")
def recommend_movies():
    payload = request.get_json(silent=True) or {}
    mood_text = str(payload.get("mood", "")).strip()
    if len(mood_text) < 2:
        return jsonify({"error": "Nasıl hissettiğini kısaca yaz."}), 400
    # The raw message remains a UI concern; only the internal interpretation
    # receives fuzzy typo tolerance so visitors never see a correction notice.
    interpreted_mood = normalize_recommendation_intent(mood_text)
    if recommendation_text_needs_clarification(interpreted_mood):
        return jsonify({"error": "İsteğini biraz daha açar mısın? Örneğin “hafif bir komedi” ya da “gerilim olmasın” diyebilirsin."}), 400
    if is_movie_fact_question(interpreted_mood):
        return jsonify({"error": "Bu alan film önerileri için. Yönetmen, oyuncu, puan ve konu sorularını Filmler Hakkında Sohbet bölümünde sorabilirsin."}), 400
    moods = detect_moods(interpreted_mood)
    try:
        ranked = tmdb_recommendation_choices(interpreted_mood)
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503
    return jsonify(
        {
            "moods": [MOOD_LABELS[mood] for mood in moods],
            "source": "tmdb",
            "recommendations": ranked,
        }
    )


@app.post("/api/zodiac-recommend")
def zodiac_recommendations():
    zodiac = (request.get_json(silent=True) or {}).get("zodiac", "")
    prompt = ZODIAC_PROMPTS.get(zodiac)
    if not prompt:
        return jsonify({"error": "Geçerli bir burç seçin."}), 400
    try:
        movies = tmdb_recommendation_choices(prompt, limit=8)
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503
    return jsonify({"zodiac": zodiac, "movies": movies})


@app.get("/api/column-previews")
def column_previews():
    previews: dict[str, Any] = {}
    used_ids: set[int] = set()
    for column in EDITORIAL_COLUMNS:
        candidates = tmdb_editorial_card_previews(column)
        movie = next((item for item in candidates if item["id"] not in used_ids), None)
        movie = movie or (candidates[0] if candidates else None)
        if movie:
            used_ids.add(movie["id"])
            previews[column["slug"]] = {
                "backdropUrl": movie.get("backdrop_url"),
                "posterUrl": movie.get("poster_url"),
                "title": movie.get("title"),
            }
    return jsonify({"previews": previews})


@app.post("/api/column-recommend")
def column_recommend():
    slug = (request.get_json(silent=True) or {}).get("slug", "")
    column = EDITORIAL_COLUMNS_BY_SLUG.get(slug)
    if not column:
        return jsonify({"error": "Geçerli bir köşe yazısı seçin."}), 400
    try:
        movies = tmdb_editorial_column_movies(column, limit=7)
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503
    return jsonify({
        "slug": slug, "category": column["category"], "title": column["title"],
        "subtitle": column["subtitle"], "intro": column["intro"],
        "why": column["why"], "movies": movies,
    })


@app.get("/api/catalog")
def catalog_movies():
    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        page = 1
    genre_ids = [value for value in request.args.get("genres", "").split(",") if value.strip().isdigit()]
    provider_ids = [value for value in request.args.get("providers", "").split(",") if value.strip().isdigit()]
    query = (request.args.get("q") or "").strip()[:120]
    sort_key = request.args.get("sort", "popular")
    runtime_gte, runtime_lte = CATALOG_RUNTIME_MAP.get(request.args.get("runtime", ""), (None, None))
    rating_value = request.args.get("rating_min") or ""
    rating_min = rating_value if rating_value in {"6", "7", "8", "9"} else None
    year_from_value = request.args.get("year_from") or ""
    year_to_value = request.args.get("year_to") or ""
    year_from = year_from_value if year_from_value.isdigit() and 1900 <= int(year_from_value) <= 2100 else None
    year_to = year_to_value if year_to_value.isdigit() and 1900 <= int(year_to_value) <= 2100 else None
    language_value = request.args.get("language") or ""
    language = language_value if language_value in {"tr", "en", "fr", "es", "it", "de", "ja", "ko"} else None
    filters = {
        "genre_ids": genre_ids,
        "sort_by": CATALOG_SORT_MAP.get(sort_key, "popularity.desc"),
        "year_from": year_from,
        "year_to": year_to,
        "vote_average_gte": rating_min,
        "runtime_gte": runtime_gte,
        "runtime_lte": runtime_lte,
        "language": language,
        "provider_ids": provider_ids,
        "vote_count_gte": 200 if sort_key == "rating" and not rating_min else 50,
    }
    try:
        if query:
            movies, total_pages = tmdb_catalog_search(query, filters, page)
        else:
            movies, total_pages = tmdb_catalog_discover(filters, page)
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503
    return jsonify({"movies": movies, "page": page, "total_pages": total_pages})


@app.get("/api/catalog/search")
def catalog_search():
    query = (request.args.get("q") or "").strip()
    if not query:
        return jsonify({"movies": [], "page": 1, "total_pages": 1})
    try:
        page = max(1, int(request.args.get("page", "1")))
    except ValueError:
        page = 1
    try:
        filters = {
            "sort_by": "popularity.desc", "genre_ids": [], "provider_ids": [],
            "vote_count_gte": 0,
        }
        movies, total_pages = tmdb_catalog_search(query, filters, page)
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503
    return jsonify({"movies": movies, "page": page, "total_pages": total_pages})


@app.get("/api/catalog/providers")
def catalog_watch_providers():
    try:
        providers = tmdb_catalog_watch_providers()
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503
    return jsonify({"region": "TR", "providers": providers})


@app.get("/api/movie/<int:movie_id>")
def movie_details(movie_id: int):
    try:
        movie = tmdb_movie_detail(movie_id)
        providers = tmdb_watch_providers(movie_id)
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503
    return jsonify({"movie": movie, "providers": providers})


@app.get("/api/movie/<int:movie_id>/trailer")
def movie_trailer(movie_id: int):
    # Kartlarda toplu istek atmamak için yalnızca ▶ butonuna basıldığında,
    # tek film için çağrılır (lazy-load). Fragman yoksa 200 + key:null döner —
    # frontend bunu "bozuk video" göstermeden sessizce ele alır.
    key = tmdb_movie_trailer_key(movie_id)
    return jsonify({"key": key})


@app.get("/api/trending")
def trending_movies():
    try:
        time_window = "day" if request.args.get("window") == "day" else "week"
        return jsonify({"source": "TMDB", "window": time_window, "movies": tmdb_trending_movies(time_window=time_window)})
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503


@app.post("/api/survey-recommend")
def survey_recommendation():
    payload = request.get_json(silent=True) or {}
    answers = payload.get("answers", [])
    # Accept the old three-answer flow too, while the current UI sends six
    # compact profile and preference answers.
    if not isinstance(answers, list) or len(answers) < 3:
        return jsonify({"error": "Anketi tamamlayın."}), 400
    summary = " · ".join(str(answer).strip() for answer in answers)
    try:
        movie = tmdb_recommendation_choices(summary, limit=1)[0]
    except RuntimeError as error:
        return jsonify({"error": str(error)}), 503
    return jsonify({"movie": movie, "summary": summary})


if __name__ == "__main__":
    # Transformers imports are not reliably thread-safe during their first load.
    # Qwen interprets requests and answers from the selected local or live catalogue.
    try:
        get_model()
    except RuntimeError:
        pass
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "7860")), debug=False)
