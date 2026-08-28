"""Local Qwen3-powered search interface for the entertainment QA data."""

from __future__ import annotations

import json
import os
import re
import threading
import csv
import random
import ssl
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from flask import Flask, jsonify, render_template, request

DATA_PATH = Path(__file__).with_name("entertainment_qa.jsonl")
MOVIES_PATH = Path(__file__).with_name("movies.json")
ENV_PATH = Path(__file__).with_name(".env")
QUIZ_FILES = {
    "Filmler": "category_movies.csv",
    "Televizyon": "category_television.csv",
    "Müzik": "category_music.csv",
    "Ünlüler": "category_celebrities.csv",
    "Eğlence": "category_entertainment.csv",
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


ENTRIES = load_entries()
QUIZ_ITEMS = load_quiz_items()
QUIZ_BY_ID = {item.id: item for item in QUIZ_ITEMS}
MOVIES = json.loads(MOVIES_PATH.read_text(encoding="utf-8"))

MOOD_KEYWORDS = {
    "relax": ("yorgun", "rahat", "sakin", "huzur", "stres", "stresli", "bunaldım", "hafif", "dingin"),
    "uplift": ("moral", "mutlu", "iyi his", "pozitif", "ilham", "umut", "keyif"),
    "funny": ("komedi", "gül", "neşeli", "eğlenceli", "komik", "kahkaha"),
    "emotional": ("duygusal", "hüzün", "hüzünlü", "ağla", "romantik", "yalnız", "yalnızım", "içe dönük", "üzgün", "mutsuz", "keyifsiz", "moralim bozuk"),
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


def rank_movies(text: str, limit: int = 3) -> list[dict[str, Any]]:
    """Rank the local film catalog before asking the LLM to word its suggestion."""
    lowered = text.lower()
    moods = detect_moods(text)

    def score(movie: dict[str, Any]) -> float:
        mood_score = sum(mood in movie["moods"] for mood in moods) * 4
        genre_score = sum(
            3 for genre, keywords in GENRE_KEYWORDS.items()
            if genre in movie["genres"] and any(keyword in lowered for keyword in keywords)
        )
        return mood_score + genre_score + random.random()

    return sorted(MOVIES, key=score, reverse=True)[:limit]


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
        "sort_by": "popularity.desc",
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
    if any(phrase in lowered for phrase in ("en iyi", "yüksek puan", "kaliteli", "imdb")):
        preferences["sort_by"] = "vote_average.desc"

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


def tmdb_recommendations(text: str, limit: int = 3) -> list[dict[str, Any]]:
    """Fetch poster-rich, Turkish movie data; local catalog is the fallback."""
    if not TMDB_API_KEY:
        return []

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
        title = result.get("title") or result.get("original_title")
        if not title:
            continue
        release_date = result.get("release_date") or ""
        genre_names = [TMDB_GENRE_NAMES.get(genre_id, "Film") for genre_id in result.get("genre_ids", [])]
        poster_path = result.get("poster_path")
        movies.append(
            {
                "id": result.get("id"),
                "title": title,
                "year": release_date[:4] or "—",
                "genres": genre_names or ["Film"],
                "moods": detect_moods(text),
                "note": result.get("overview") or "Bu film için Türkçe açıklama henüz bulunmuyor.",
                "rating": result.get("vote_average"),
                "poster_url": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None,
            }
        )
        if len(movies) == limit:
            break
    return movies


def movie_candidates(text: str, limit: int = 3) -> list[dict[str, Any]]:
    return tmdb_recommendations(text, limit) or rank_movies(text, limit)


def ask_movie_bot(message: str, choices: list[dict[str, Any]]) -> str:
    """Constrained local-LLM reply: it may only recommend from our catalog."""
    model, tokenizer = get_model()
    from mlx_lm import generate

    catalog = "\n".join(
        f"- {movie['title']} ({movie['year']}) | {', '.join(movie['genres'])} | {movie['note']}"
        for movie in choices
    )
    messages = [
        {
            "role": "system",
            "content": (
                "Sen Lûme adlı Türkçe film öneri chatbotusun. Kullanıcının mesajındaki ruh hali, "
                "enerji ve tür isteğine cevap ver. Yalnızca sana verilen yerel katalogdaki filmleri "
                "öner; katalog dışından film adı uydurma. En iyi 1-2 filmi seç, neden uygun olduğunu "
                "en fazla 2 kısa cümlede, markdown ya da madde işareti olmadan sıcak ve net biçimde anlat. Trivia sorusu sorulursa da filmi önerme "
                "odağında kal ve uygun bir tercih öner."
            ),
        },
        {"role": "user", "content": f"Kullanıcı mesajı: {message}\n\nYerel film kataloğu:\n{catalog}"},
    ]
    prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True, enable_thinking=False)
    with _generation_lock:
        return generate(model, tokenizer, prompt=prompt, max_tokens=110, verbose=False).strip()


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


@app.get("/")
def index() -> str:
    return render_template("index.html", entries=len(ENTRIES))


@app.get("/api/health")
def health():
    return jsonify(
        {
            "entries": len(ENTRIES),
            "quizItems": len(QUIZ_ITEMS),
            "translatedQuizItems": len(QUIZ_TRANSLATIONS),
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


@app.post("/api/search")
def search():
    query = (request.get_json(silent=True) or {}).get("query", "").strip()
    if len(query) < 2:
        return jsonify({"error": "Lütfen en az iki karakter yazın."}), 400

    recommendations = movie_candidates(query)
    try:
        answer = ask_movie_bot(query, recommendations)
        generated = True
    except RuntimeError:
        names = ", ".join(movie["title"] for movie in recommendations[:2])
        answer = f"Bunun için yerel katalogdan {names} iyi bir başlangıç olur. Özellikle ilk seçenek ruh haline daha yakın görünüyor."
        generated = False

    return jsonify(
        {
            "answer": answer,
            "generated": generated,
            "mode": "film-bot",
            "matches": [
                {"question": f"{movie['title']} · {movie['year']}", "answer": movie["note"]}
                for movie in recommendations
            ],
        }
    )


@app.get("/api/quiz")
def quiz_question():
    # Prefer cards whose Turkish rendering succeeded; never make an English fallback sticky.
    item = random.choice(QUIZ_ITEMS)
    translated = translated_quiz_content(item)
    for _ in range(2):
        if translated["version"] == 2:
            break
        item = random.choice(QUIZ_ITEMS)
        translated = translated_quiz_content(item)
    choices = list(zip(item.choices, translated["choices"]))
    random.shuffle(choices)
    return jsonify(
        {
            "id": item.id,
            "category": item.category,
            "question": translated["question"],
            "choices": [original for original, _ in choices],
            "displayChoices": [display for _, display in choices],
        }
    )


@app.post("/api/quiz/check")
def check_quiz_answer():
    payload = request.get_json(silent=True) or {}
    item = QUIZ_BY_ID.get(payload.get("id"))
    if item is None:
        return jsonify({"error": "Soru bulunamadı. Lütfen yeni bir soru açın."}), 404
    selected = str(payload.get("choice", "")).strip()
    translated = translated_quiz_content(item)
    answer_index = item.choices.index(item.answer)
    return jsonify(
        {
            "correct": selected == item.answer,
            "answer": item.answer,
            "answerDisplay": translated["choices"][answer_index],
        }
    )


@app.post("/api/recommend")
def recommend_movies():
    mood_text = (request.get_json(silent=True) or {}).get("mood", "").strip()
    if len(mood_text) < 2:
        return jsonify({"error": "Nasıl hissettiğini kısaca yaz."}), 400
    moods = detect_moods(mood_text)
    ranked = movie_candidates(mood_text)
    return jsonify(
        {
            "moods": [MOOD_LABELS[mood] for mood in moods],
            "recommendations": ranked,
        }
    )


@app.post("/api/survey-recommend")
def survey_recommendation():
    payload = request.get_json(silent=True) or {}
    answers = payload.get("answers", [])
    # Accept the old three-answer flow too, while the current UI sends six
    # compact profile and preference answers.
    if not isinstance(answers, list) or len(answers) < 3:
        return jsonify({"error": "Anketi tamamlayın."}), 400
    summary = " · ".join(str(answer).strip() for answer in answers)
    movie = movie_candidates(summary, limit=1)[0]
    return jsonify({"movie": movie, "summary": summary})


if __name__ == "__main__":
    # Transformers imports are not reliably thread-safe during their first load.
    # Initialise Qwen first, then build the semantic index in the background.
    try:
        get_model()
    except RuntimeError:
        pass
    start_semantic_load()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "7860")), debug=False)
