#!/usr/bin/env python3
"""Unified fetcher for all external data sources used by Al-Furqan.

One entry point, one file. Each source is a subcommand with its own flags
and its own implementation. Heavy dependencies (youtube_transcript_api,
yt_dlp, datasets, elasticsearch) are imported lazily inside the source
functions so you only need them installed for the sources you actually run.

All fetchers (except tafsirs) write event records directly to the canonical
training JSONL files; they do not produce intermediate JSON corpora. Runs are
idempotent: each source scans the target JSONL for existing event_ids on
startup and only appends new records.

Supported sources:
    wikipedia  - Wikipedia REST API articles   -> "written" JSONL (chunked events)
    gutenberg  - Project Gutenberg books       -> "written" JSONL (chunked events)
    youtube    - YouTube playlist transcripts  -> "talk"    JSONL (one event per episode)
    tafsirs    - MohamedRashad/Quran-Tafseer HF dataset -> Elasticsearch

Target JSONL files:
    written = data_archive/training/testing/model_testing_how_people_write_about_history.jsonl
    talk    = data_archive/training/testing/model_testing_how_people_talk_about_history.jsonl

Usage:
    python fetch_data.py wikipedia
    python fetch_data.py gutenberg --out custom.jsonl
    python fetch_data.py youtube https://www.youtube.com/playlist?list=... --delay 2
    python fetch_data.py tafsirs --priority P0 --dry-run
    python fetch_data.py tafsirs --list-books
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import random
import re
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

from al_furqan import setup_logging
from al_furqan.paths import (
    DATA_TRAINING_TESTING,
    PROJECT_ROOT,
    TESTING_TALK_ABOUT_HISTORY_JSONL as TALK_JSONL,
)

logger = logging.getLogger(__name__)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Canonical training JSONL targets. Fetchers append event records directly
# to these files (append-mode, deduplicated by event_id).
WRITTEN_JSONL = DATA_TRAINING_TESTING / "model_testing_how_people_write_about_history.jsonl"

# Chunk sizes match the training/pipeline/generators/human_history.py contract
# so events land in the same shape regardless of which pipeline produced them.
WIKIPEDIA_CHUNK_CHARS = 6000
GUTENBERG_CHUNK_CHARS = 8000


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _http_get(url: str, timeout: int = 60) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def _slugify(title: str, max_len: int = 50) -> str:
    """Match the slug shape used by training/pipeline/generators/human_history.py."""
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")[:max_len]


def _load_existing_event_ids(path: Path) -> set[str]:
    """Scan a JSONL file and return every event_id present.

    Returns an empty set if the file doesn't exist yet. Malformed lines are
    skipped with a warning so a corrupt tail doesn't block a re-run.
    """
    if not path.exists():
        return set()
    ids: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                logger.warning("Skipping malformed JSONL line %d in %s", lineno, path.name)
                continue
            eid = obj.get("event_id")
            if eid:
                ids.add(eid)
    return ids


def _append_event(path: Path, event: dict) -> None:
    """Append a single event to a JSONL file, adding the edge_counts field.

    Matches the writer in training/pipeline/generators/human_history.py so
    the two producers stay schema-compatible.
    """
    edge_counts: dict[str, int] = {}
    for edge in event.get("edges", []):
        edge_counts[edge["edge_type"]] = edge_counts.get(edge["edge_type"], 0) + 1
    event["edge_counts"] = edge_counts
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


# ===========================================================================
# SOURCE: Wikipedia
# ===========================================================================

WIKIPEDIA_TITLES: list[str] = [
    # Battles
    "Battle_of_Badr", "Battle_of_Uhud", "Battle_of_the_Trench",
    "Siege_of_Constantinople_(1453)", "Battle_of_Manzikert",
    "Battle_of_Ain_Jalut", "Battle_of_Lepanto", "Battle_of_Vienna_(1683)",
    "Battle_of_Waterloo", "Battle_of_Stalingrad", "Battle_of_Midway",
    "Battle_of_Gettysburg", "Battle_of_Verdun", "Battle_of_the_Somme",
    "Battle_of_Gallipoli", "Battle_of_El_Alamein",
    # Civilizations
    "Indus_Valley_Civilisation", "Sumer", "Phoenicia", "Ancient_Israel",
    "Kingdom_of_Kush", "Great_Zimbabwe", "Benin_Empire",
    "Ethiopian_Empire", "Majapahit", "Srivijaya",
    "Chola_dynasty", "Vijayanagara_Empire",
    "Almohad_Caliphate", "Almoravid_dynasty",
    "Sokoto_Caliphate", "Durrani_Empire", "Zulu_Kingdom",
    # Colonial
    "Berlin_Conference", "Belgian_Congo",
    "French_Algeria", "Apartheid",
    "Indian_independence_movement", "Indonesian_National_Revolution",
    "Algerian_War", "Mau_Mau_Uprising",
    "Congo_Crisis", "Nigerian_Civil_War",
    # Economics
    "Keynesian_economics", "Monetarism", "Austrian_School",
    "Bretton_Woods_system", "Nixon_shock", "Plaza_Accord",
    "Petrodollar_recycling", "Quantitative_easing",
    "Austerity", "Structural_adjustment",
    "Currency_war", "Trade_war",
    # Treaties
    "Treaty_of_Tordesillas", "Treaty_of_Utrecht",
    "Treaty_of_Nanking", "Unequal_treaty",
    "San_Remo_conference", "Treaty_of_Lausanne",
    "Atlantic_Charter", "United_Nations_Charter",
    "Helsinki_Accords", "Maastricht_Treaty",
    # Covert ops
    "Phoenix_program", "COINTELPRO",
    "Contras", "Operation_Cyclone",
    "Extraordinary_rendition",
    "Abu_Ghraib_torture_and_prisoner_abuse",
    "Guantanamo_Bay_detention_camp",
    # Modern conflicts
    "First_Chechen_War", "Second_Chechen_War",
    "Somali_Civil_War",
    "Tigray_War", "South_Sudanese_Civil_War",
    "Boko_Haram_insurgency",
    "Islamic_State_of_Iraq_and_the_Levant",
    # Political systems
    "Republicanism", "Constitutionalism", "Federalism",
    "Separation_of_powers", "Parliamentary_system",
    "Oligarchy", "Plutocracy", "Kleptocracy",
    "Failed_state", "Deep_state",
    # International law
    "Geneva_Conventions", "Nuremberg_trials",
    "International_Criminal_Court",
    "Universal_Declaration_of_Human_Rights",
    "Responsibility_to_protect",
    # Media
    "Yellow_journalism", "War_propaganda",
    "Manufacturing_Consent", "Propaganda_model",
    "Disinformation", "Fake_news",
    # Technology
    "Manhattan_Project", "Green_Revolution",
    "Information_Age", "Surveillance_capitalism",
    # Key figures
    "Cyrus_the_Great", "Hannibal_Barca",
    "Umar", "Harun_al-Rashid",
    "Tamerlane", "Babur", "Akbar",
    "Elizabeth_I", "Louis_XIV",
    "Peter_the_Great", "Catherine_the_Great",
    "Simon_Bolivar", "Toussaint_Louverture",
    "Abraham_Lincoln", "Karl_Marx", "Vladimir_Lenin",
    "Mustafa_Kemal_Ataturk", "Reza_Shah",
    "David_Ben-Gurion", "Gamal_Abdel_Nasser",
    "Jawaharlal_Nehru", "Sukarno", "Kwame_Nkrumah",
    "Patrice_Lumumba", "Thomas_Sankara",
    "Saddam_Hussein", "Muammar_Gaddafi",
    "Xi_Jinping", "Vladimir_Putin", "Recep_Tayyip_Erdogan",
    # Rise and fall
    "Fall_of_the_Western_Roman_Empire",
    "Collapse_of_the_Soviet_Union",
    "End_of_apartheid_in_South_Africa",
    "Breakup_of_Yugoslavia",
    # Philosophy of history
    "Historiography", "Philosophy_of_history",
    "Historical_materialism", "Clash_of_Civilizations",
    "World-systems_theory", "Dependency_theory",
    # Genocide
    "Armenian_genocide", "Holodomor",
    "Cambodian_genocide", "Nanjing_Massacre",
    "Transatlantic_slave_trade", "Congo_Free_State",
    # Migrations
    "Palestinian_exodus", "Partition_of_India",
    "European_migrant_crisis", "Syrian_refugee_crisis",
    # More economics
    "History_of_money", "Central_bank", "Federal_Reserve",
    "Bank_of_England", "World_Bank_Group",
    "International_Monetary_Fund", "Asian_Infrastructure_Investment_Bank",
    # Propaganda
    "Edward_Bernays", "Walter_Lippmann", "Noam_Chomsky",
    "Public_relations", "Spin_(propaganda)",
]


def _extract_wiki(html: str) -> str:
    text = re.sub(r"<ref[^>]*>.*?</ref>", "", html, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", "\n", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    text = re.sub(r"\[\d+\]", "", text)
    lines = [l.strip() for l in text.split("\n") if len(l.strip()) > 10]
    return "\n".join(lines)


def fetch_wikipedia(args: argparse.Namespace) -> None:
    out_path: Path = args.out or WRITTEN_JSONL
    existing_ids = _load_existing_event_ids(out_path)
    logger.info("Target: %s", out_path.relative_to(PROJECT_ROOT))
    logger.info("Existing event_ids: %d", len(existing_ids))

    titles_added = 0
    events_added = 0
    for title in WIKIPEDIA_TITLES:
        clean_title = title.replace("_", " ").replace("%27", "'")
        slug = _slugify(clean_title)
        # Cheap pre-check: if the first chunk is already present, skip the HTTP fetch
        if f"wikipedia:{slug}:01" in existing_ids:
            continue
        try:
            html = _http_get(f"https://en.wikipedia.org/api/rest_v1/page/html/{title}")
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.debug("  skip %s: %s", title, e)
            continue

        content = _extract_wiki(html)
        if len(content) < 300:
            continue

        url = f"https://en.wikipedia.org/wiki/{title}"
        num_chunks = max(1, (len(content) + WIKIPEDIA_CHUNK_CHARS - 1) // WIKIPEDIA_CHUNK_CHARS)
        wrote_title = False
        for idx in range(num_chunks):
            chunk = content[idx * WIKIPEDIA_CHUNK_CHARS:(idx + 1) * WIKIPEDIA_CHUNK_CHARS].strip()
            if len(chunk) < 200:
                continue
            event_id = f"wikipedia:{slug}:{idx + 1:02d}"
            if event_id in existing_ids:
                continue
            _append_event(out_path, {
                "event_id": event_id,
                "source": "wikipedia",
                "source_detail": url,
                "name": clean_title if idx == 0 else f"{clean_title} (part {idx + 1})",
                "year": None,
                "period": "contemporary",
                "country": "",
                "event_type": "encyclopedia",
                "location": "",
                "edges": [{
                    "edge_type": "content",
                    "data": {
                        "title": clean_title,
                        "section": idx + 1,
                        "total_sections": num_chunks,
                        "text": chunk,
                        "char_count": len(chunk),
                        "url": url,
                    },
                }],
            })
            existing_ids.add(event_id)
            events_added += 1
            wrote_title = True

        if wrote_title:
            titles_added += 1
            if titles_added % 10 == 0:
                logger.info("  +%d titles, +%d events so far", titles_added, events_added)

        time.sleep(0.15)

    logger.info("Wikipedia: +%d titles, +%d events appended to %s",
                titles_added, events_added, out_path.relative_to(PROJECT_ROOT))


def _add_wikipedia_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "wikipedia",
        help="Append Wikipedia article chunks to the 'written' JSONL",
    )
    p.add_argument(
        "--out", type=Path, default=None,
        help=f"Target JSONL (default: {WRITTEN_JSONL.relative_to(PROJECT_ROOT)})",
    )
    p.set_defaults(func=fetch_wikipedia)


# ===========================================================================
# SOURCE: Project Gutenberg
# ===========================================================================

GUTENBERG_BOOKS: list[tuple[int, str]] = [
    # Gibbon - Decline and Fall of Roman Empire (6 volumes)
    (25717, "Decline Fall Roman Empire V1"),
    (25718, "Decline Fall Roman Empire V2"),
    (25719, "Decline Fall Roman Empire V3"),
    (25720, "Decline Fall Roman Empire V4"),
    (25721, "Decline Fall Roman Empire V5"),
    (25722, "Decline Fall Roman Empire V6"),
    # Mommsen - History of Rome (5 volumes)
    (10740, "History of Rome V1 Mommsen"),
    (10741, "History of Rome V2 Mommsen"),
    (10742, "History of Rome V3 Mommsen"),
    (10743, "History of Rome V4 Mommsen"),
    (10744, "History of Rome V5 Mommsen"),
    # Macaulay - History of England (4 volumes)
    (30168, "History of England V1 Macaulay"),
    (30169, "History of England V2 Macaulay"),
    (30170, "History of England V3 Macaulay"),
    (30171, "History of England V4 Macaulay"),
    # Motley - Rise of Dutch Republic (3 volumes)
    (15595, "Rise Dutch Republic V1"),
    (15596, "Rise Dutch Republic V2"),
    (15597, "Rise Dutch Republic V3"),
    # Political philosophy
    (3207, "Leviathan Hobbes"),
    (7370, "Republic Plato"),
    (1404, "The Prince Machiavelli"),
    (2680, "Meditations Marcus Aurelius"),
    (10900, "Art of War Sun Tzu"),
    (6762, "Two Treatises Government Locke"),
    (7416, "Social Contract Rousseau"),
    (5827, "Communist Manifesto"),
    (3600, "On Liberty Mill"),
    (3076, "Spirit of Laws Montesquieu"),
    (7142, "Federalist Papers"),
    (8438, "Utopia Thomas More"),
    (6049, "Discourses on Livy Machiavelli"),
    # Economics
    (1250, "Wealth of Nations Smith"),
    (10800, "Wealth of Nations Books 2-3"),
    (35588, "Economic Consequences Peace Keynes"),
    (36382, "Economic Interpretation Constitution Beard"),
    # War & strategy
    (30610, "On War Clausewitz"),
    (5400, "Gallic Wars Caesar"),
    # Revolution & reform
    (12593, "Reflections on Revolution Burke"),
    (22585, "Age of Reason Paine"),
    (37, "Common Sense Paine"),
    (3743, "Rights of Man Paine"),
    (17208, "Origin Family Engels"),
    # History
    (10616, "Peloponnesian War Thucydides"),
    (39452, "Histories Herodotus"),
    (11030, "Annals Tacitus"),
    (16316, "Parallel Lives Plutarch V1"),
    (34901, "Civilization England V1 Buckle"),
    (34902, "Civilization England V2 Buckle"),
    (2741, "Democracy America V1 Tocqueville"),
    (815, "Democracy America V2 Tocqueville"),
    (16000, "History of Egypt V1"),
    (16001, "History of Egypt V2"),
    (33504, "Story Moors in Spain"),
    (16259, "History Conquest Egypt"),
    (10681, "Conquest of Peru"),
    (14140, "Conquest of Mexico V1"),
    (13316, "History of Rome Bury"),
    (18569, "Civilization Renaissance Italy"),
    (20671, "Short History World Wells"),
    (18994, "History Papacy V1"),
    # Psychology & sociology
    (40121, "The Crowd Gustave Le Bon"),
    (5736, "Sociology Modern Social Problems"),
    (36495, "Propaganda Bernays"),
    # Philosophy
    (4705, "Treatise Human Nature Hume"),
    (46424, "New Atlantis Bacon"),
    (3032, "Subjection Women Mill"),
    # Biography & memoir
    (8091, "Autobiography Franklin"),
    (9662, "Autobiography Darwin"),
    # Ancient texts
    (4367, "Koran Palmer"),
    (2250, "Koran Sale"),
    # More
    (13726, "Persian Letters Montesquieu"),
    (38427, "Idea of Progress"),
    (6469, "History Friedrich II Prussia V1"),
    (10833, "Outline Science V1"),
    (12106, "Story Great War V1"),
    (20108, "History French Revolution Carlyle"),
    (13644, "History Napoleon Bonaparte V1"),
    (13645, "History Napoleon Bonaparte V2"),
    (4925, "Confessions Augustine"),
    (10615, "City of God Augustine"),
    (19498, "Story of Mankind Van Loon"),
]


def _fetch_gutenberg_book(book_id: int) -> str | None:
    for url in (
        f"https://www.gutenberg.org/cache/epub/{book_id}/pg{book_id}.txt",
        f"https://www.gutenberg.org/files/{book_id}/{book_id}-0.txt",
    ):
        try:
            text = _http_get(url)
        except Exception:  # pylint: disable=broad-exception-caught
            continue
        start = text.find("*** START OF")
        if start < 0:
            start = text.find("***START OF")
        end = text.find("*** END OF")
        if end < 0:
            end = text.find("***END OF")
        if start > 0 and end > start:
            return text[start:end]
        if start > 0:
            return text[start:]
        if len(text) > 5000:
            return text
    return None


def fetch_gutenberg(args: argparse.Namespace) -> None:
    out_path: Path = args.out or WRITTEN_JSONL
    existing_ids = _load_existing_event_ids(out_path)
    logger.info("Target: %s", out_path.relative_to(PROJECT_ROOT))
    logger.info("Existing event_ids: %d", len(existing_ids))

    books_added = 0
    events_added = 0
    for book_id, title in GUTENBERG_BOOKS:
        slug = _slugify(title)
        if f"gutenberg:{slug}:01" in existing_ids:
            continue

        text = _fetch_gutenberg_book(book_id)
        if not text or len(text) < 5000:
            logger.warning("  FAIL: %s", title)
            time.sleep(1)
            continue

        num_chunks = max(1, (len(text) + GUTENBERG_CHUNK_CHARS - 1) // GUTENBERG_CHUNK_CHARS)
        wrote_book = False
        source_detail = f"https://www.gutenberg.org/ebooks/{book_id}"
        for idx in range(num_chunks):
            chunk = text[idx * GUTENBERG_CHUNK_CHARS:(idx + 1) * GUTENBERG_CHUNK_CHARS].strip()
            if len(chunk) < 200:
                continue
            event_id = f"gutenberg:{slug}:{idx + 1:02d}"
            if event_id in existing_ids:
                continue
            _append_event(out_path, {
                "event_id": event_id,
                "source": "gutenberg",
                "source_detail": source_detail,
                "name": title if idx == 0 else f"{title} (part {idx + 1})",
                "year": None,
                "period": "historical",
                "country": "",
                "event_type": "historical_text",
                "location": "",
                "edges": [{
                    "edge_type": "content",
                    "data": {
                        "title": title,
                        "section": idx + 1,
                        "total_sections": num_chunks,
                        "text": chunk,
                        "char_count": len(chunk),
                        "url": source_detail,
                    },
                }],
            })
            existing_ids.add(event_id)
            events_added += 1
            wrote_book = True

        if wrote_book:
            books_added += 1
            logger.info("  OK: %s (%d sections, %s chars)",
                        title, num_chunks, f"{len(text):,}")
        time.sleep(1)

    logger.info("Gutenberg: +%d books, +%d events appended to %s",
                books_added, events_added, out_path.relative_to(PROJECT_ROOT))


def _add_gutenberg_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "gutenberg",
        help="Append Project Gutenberg book chunks to the 'written' JSONL",
    )
    p.add_argument(
        "--out", type=Path, default=None,
        help=f"Target JSONL (default: {WRITTEN_JSONL.relative_to(PROJECT_ROOT)})",
    )
    p.set_defaults(func=fetch_gutenberg)


# ===========================================================================
# SOURCE: YouTube playlist transcripts
# ===========================================================================

YOUTUBE_DEFAULT_PLAYLIST = "https://www.youtube.com/playlist?list=PLYa964dzJh1J545AyFlLepb2Prert15te"
YOUTUBE_MAX_RETRIES_PER_VIDEO = 5

# playlist_id -> (event_id_prefix, source name used in the JSONL `source` field)
YOUTUBE_PLAYLIST_SHOWS: dict[str, tuple[str, str]] = {
    "PLYa964dzJh1J545AyFlLepb2Prert15te": ("tucker", "the_tucker_carlson_show"),
    "PLq24DlPvfmfoYpZvF0ATdHPZPGnwofq8a": ("pierce_morgan", "pierce_morgan_show"),
}


def _get_webshare_proxies() -> list[tuple[str, str, int, str, str]]:
    user = os.environ.get("WEBSHARE_USER", "")
    pw = os.environ.get("WEBSHARE_PASS", "")
    return [
        ("http", "147.161.210.140", 8800, "", ""),
        ("http", "5.104.87.17", 8051, "", ""),
        ("http", "167.103.115.102", 8800, "", ""),
        ("http", "152.32.132.190", 7890, "", ""),
        ("http", "217.52.247.69", 1976, "", ""),
        ("http", "31.59.20.176", 6754, user, pw),
        ("http", "198.23.239.134", 6540, user, pw),
        ("http", "45.38.107.97", 6014, user, pw),
        ("http", "107.172.163.27", 6543, user, pw),
        ("http", "198.105.121.200", 6462, user, pw),
        ("http", "216.10.27.159", 6837, user, pw),
        ("http", "142.111.67.146", 5611, user, pw),
        ("http", "191.96.254.138", 6185, user, pw),
        ("http", "31.58.9.4", 6077, user, pw),
        ("http", "198.46.161.42", 5092, user, pw),
    ]


def _build_proxy_url(ws_proxy: tuple[str, str, int, str, str]) -> str:
    scheme, host, port, user, pw = ws_proxy
    if user and pw:
        return f"{scheme}://{user}:{pw}@{host}:{port}"
    return f"{scheme}://{host}:{port}"


def _get_youtube_show(playlist_url: str) -> tuple[str, str]:
    """Return (event_id_prefix, source_name) for the playlist.

    Falls back to a generic prefix built from the playlist id so unknown
    playlists still produce stable event_ids.
    """
    for playlist_id, show in YOUTUBE_PLAYLIST_SHOWS.items():
        if playlist_id in playlist_url:
            return show
    m = re.search(r"list=([a-zA-Z0-9_-]+)", playlist_url)
    if m:
        pid = m.group(1).lower().replace("-", "_")
        return (f"yt_{pid[:16]}", f"youtube_{pid[:40]}")
    return ("yt_unknown", "youtube_unknown")


def _clean_snippet_text(text: str | None) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _get_youtube_playlist_videos(playlist_url: str) -> list[dict]:
    from yt_dlp import YoutubeDL  # pylint: disable=import-outside-toplevel

    ydl = YoutubeDL({
        'quiet': True,
        'flat_playlist': True,
        'extract_flat': True,
        'ignoreerrors': True,
        'no_warnings': True,
    })
    result = ydl.extract_info(playlist_url, download=False)
    videos = []
    if result and 'entries' in result:
        for v in result['entries']:
            if v and v.get('id'):
                videos.append({
                    'id': v['id'],
                    'title': v.get('title', v['id']),
                    'duration': v.get('duration') or 0,
                })
    return videos


def fetch_youtube(args: argparse.Namespace) -> None:
    from youtube_transcript_api import YouTubeTranscriptApi  # pylint: disable=import-outside-toplevel
    from youtube_transcript_api.proxies import GenericProxyConfig  # pylint: disable=import-outside-toplevel

    playlist_url: str = args.playlist_url
    delay: int = args.delay
    use_proxies: bool = not args.no_proxy

    out_path: Path = args.out or TALK_JSONL
    event_prefix, source_name = _get_youtube_show(playlist_url)
    existing_ids = _load_existing_event_ids(out_path)

    logger.info("Target: %s", out_path.relative_to(PROJECT_ROOT))
    logger.info("Show: %s (prefix=%s)", source_name, event_prefix)
    logger.info("Existing event_ids (across all shows): %d", len(existing_ids))

    webshare_proxies = _get_webshare_proxies()
    logger.info("Available proxies: %d", len(webshare_proxies))

    videos = _get_youtube_playlist_videos(playlist_url)
    logger.info("Total videos: %d", len(videos))

    if not videos:
        logger.warning("No videos found!")
        return

    proxy_pool = list(webshare_proxies)
    if use_proxies:
        random.shuffle(proxy_pool)

    proxy_idx = 0
    success = 0
    skipped = 0
    errors = 0

    for i, v in enumerate(videos):
        video_id = v["id"]
        title = v["title"]
        duration = v.get("duration", 0) or 0

        if args.min_duration and duration and duration < args.min_duration:
            logger.info("[%d/%d] Skipping short (%ds): %s...",
                        i + 1, len(videos), duration, title[:50])
            skipped += 1
            continue

        if "[Private video]" in title:
            logger.info("[%d/%d] Skipping private: %s...", i + 1, len(videos), title[:50])
            skipped += 1
            continue

        episode_slug = _slugify(title, max_len=50)
        event_id = f"{event_prefix}:{episode_slug}"
        if event_id in existing_ids:
            logger.info("[%d/%d] Skipping existing: %s...", i + 1, len(videos), title[:50])
            skipped += 1
            continue

        snippets = None
        last_error: Exception | None = None

        attempts = YOUTUBE_MAX_RETRIES_PER_VIDEO if use_proxies else 1
        for attempt in range(attempts):
            if use_proxies:
                ws_proxy = proxy_pool[proxy_idx % len(proxy_pool)]
                proxy_idx += 1
                proxy_url = _build_proxy_url(ws_proxy)
                logger.info(
                    "[%d/%d] Fetching: %s... (attempt %d/%d, proxy %s:%d)",
                    i + 1, len(videos), title[:50], attempt + 1, attempts,
                    ws_proxy[1], ws_proxy[2],
                )
                try:
                    proxy_config = GenericProxyConfig(http_url=proxy_url, https_url=proxy_url)
                    ytt_api = YouTubeTranscriptApi(proxy_config=proxy_config)
                    snippets = ytt_api.fetch(video_id).snippets
                    break
                except Exception as e:  # pylint: disable=broad-exception-caught
                    last_error = e
                    logger.warning("  -> proxy attempt %d failed: %s", attempt + 1, str(e)[:80])
                    continue
            else:
                logger.info("[%d/%d] Fetching: %s... (no proxy)", i + 1, len(videos), title[:50])
                try:
                    ytt_api = YouTubeTranscriptApi()
                    snippets = ytt_api.fetch(video_id).snippets
                    break
                except Exception as e:  # pylint: disable=broad-exception-caught
                    last_error = e
                    logger.warning("  -> direct fetch failed: %s", str(e)[:80])
                    break

        if snippets is None:
            logger.error(
                "  -> Giving up on %s after %d attempts: %s",
                video_id, attempts,
                str(last_error)[:80] if last_error else "unknown",
            )
            errors += 1
            continue

        full_text = " ".join(
            _clean_snippet_text(s.text) for s in snippets
            if _clean_snippet_text(s.text)
        ).strip()
        if len(full_text) < 300:
            logger.warning("  -> transcript too short (%d chars), skipping", len(full_text))
            errors += 1
            continue

        _append_event(out_path, {
            "event_id": event_id,
            "source": source_name,
            "source_detail": title,
            "name": title,
            "year": None,
            "period": "contemporary",
            "country": "US",
            "event_type": "political_commentary",
            "location": "",
            "edges": [{
                "edge_type": "content",
                "data": {
                    "title": title,
                    "text": full_text,
                    "char_count": len(full_text),
                    "episode_slug": episode_slug,
                },
            }],
        })
        existing_ids.add(event_id)
        success += 1
        logger.info("  -> Appended: %d chars", len(full_text))

        time.sleep(delay)

    logger.info("Done! Appended: %d, Skipped: %d, Errors: %d", success, skipped, errors)


def _add_youtube_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "youtube",
        help="Append YouTube playlist transcripts to the 'talk' JSONL (one event per episode)",
    )
    p.add_argument("playlist_url", nargs="?", default=YOUTUBE_DEFAULT_PLAYLIST,
                   help="YouTube playlist URL")
    p.add_argument("--out", type=Path, default=None,
                   help=f"Target JSONL (default: {TALK_JSONL.relative_to(PROJECT_ROOT)})")
    p.add_argument("--delay", type=int, default=2, help="Delay between requests (seconds)")
    p.add_argument("--no-proxy", action="store_true", help="Run without proxies")
    p.add_argument("--min-duration", type=int, default=0,
                   help="Skip videos shorter than N seconds (0 = no filter)")
    p.set_defaults(func=fetch_youtube)


# ===========================================================================
# SOURCE: Tafsirs (HuggingFace -> Elasticsearch)
# ===========================================================================

TAFSIRS_DEFAULT_INDEX = "furqan_tafsir_structural"

SURAH_MAP: dict[str, int] = {
    "سورة الفاتحة": 1, "سورة البقرة": 2, "سورة آل عمران": 3, "سورة النساء": 4,
    "سورة المائدة": 5, "سورة الأنعام": 6, "سورة الأعراف": 7, "سورة الأنفال": 8,
    "سورة التوبة": 9, "سورة يونس": 10, "سورة هود": 11, "سورة يوسف": 12,
    "سورة الرعد": 13, "سورة إبراهيم": 14, "سورة الحجر": 15, "سورة النحل": 16,
    "سورة الإسراء": 17, "سورة الكهف": 18, "سورة مريم": 19, "سورة طه": 20,
    "سورة الأنبياء": 21, "سورة الحج": 22, "سورة المؤمنون": 23, "سورة النور": 24,
    "سورة الفرقان": 25, "سورة الشعراء": 26, "سورة النمل": 27, "سورة القصص": 28,
    "سورة العنكبوت": 29, "سورة الروم": 30, "سورة لقمان": 31, "سورة السجدة": 32,
    "سورة الأحزاب": 33, "سورة سبأ": 34, "سورة فاطر": 35, "سورة يس": 36,
    "سورة الصافات": 37, "سورة ص": 38, "سورة الزمر": 39, "سورة غافر": 40,
    "سورة فصلت": 41, "سورة الشورى": 42, "سورة الزخرف": 43, "سورة الدخان": 44,
    "سورة الجاثية": 45, "سورة الأحقاف": 46, "سورة محمد": 47, "سورة الفتح": 48,
    "سورة الحجرات": 49, "سورة ق": 50, "سورة الذاريات": 51, "سورة الطور": 52,
    "سورة النجم": 53, "سورة القمر": 54, "سورة الرحمن": 55, "سورة الواقعة": 56,
    "سورة الحديد": 57, "سورة المجادلة": 58, "سورة الحشر": 59, "سورة الممتحنة": 60,
    "سورة الصف": 61, "سورة الجمعة": 62, "سورة المنافقون": 63, "سورة التغابن": 64,
    "سورة الطلاق": 65, "سورة التحريم": 66, "سورة الملك": 67, "سورة القلم": 68,
    "سورة الحاقة": 69, "سورة المعارج": 70, "سورة نوح": 71, "سورة الجن": 72,
    "سورة المزمل": 73, "سورة المدثر": 74, "سورة القيامة": 75, "سورة الإنسان": 76,
    "سورة المرسلات": 77, "سورة النبأ": 78, "سورة النازعات": 79, "سورة عبس": 80,
    "سورة التكوير": 81, "سورة الانفطار": 82, "سورة المطففين": 83, "سورة الانشقاق": 84,
    "سورة البروج": 85, "سورة الطارق": 86, "سورة الأعلى": 87, "سورة الغاشية": 88,
    "سورة الفجر": 89, "سورة البلد": 90, "سورة الشمس": 91, "سورة الليل": 92,
    "سورة الضحى": 93, "سورة الشرح": 94, "سورة التين": 95, "سورة العلق": 96,
    "سورة القدر": 97, "سورة البينة": 98, "سورة الزلزلة": 99, "سورة العاديات": 100,
    "سورة القارعة": 101, "سورة التكاثر": 102, "سورة العصر": 103, "سورة الهمزة": 104,
    "سورة الفيل": 105, "سورة قريش": 106, "سورة الماعون": 107, "سورة الكوثر": 108,
    "سورة الكافرون": 109, "سورة النصر": 110, "سورة المسد": 111, "سورة الإخلاص": 112,
    "سورة الفلق": 113, "سورة الناس": 114,
}

# Priority tafsir groups; each inner list holds acceptable substring patterns
PRIORITY_TAFSIRS: dict[str, list[list[str]]] = {
    "P0": [
        ["نظم الدرر"],                              # al-Biqa'i
        ["التحرير والتنوير"],                        # Ibn Ashur
        ["مفاتيح الغيب", "التفسير الكبير"],          # al-Razi (Fakhr al-Din)
    ],
    "P1": [
        ["الكشاف"],                                  # al-Zamakhshari
        ["البحر المحيط"],                            # Abu Hayyan
        ["السعدي", "تيسير الكريم"],                  # al-Saadi
    ],
    "P2": [
        ["الميزان"],                                 # al-Tabatabai
        ["جامع البيان", "تفسير الطبري"],              # al-Tabari
        ["الجامع لاحكام", "القرطبي"],                # al-Qurtubi
    ],
}

# NOTE: في ظلال القرآن (Sayyid Qutb) is NOT in the MohamedRashad/Quran-Tafseer
# HuggingFace dataset. It must be sourced separately.

_TAFSIR_AYAH_NUM_RE = re.compile(r"(\d+)")

# Arabic diacritics Unicode range (fatha, damma, kasra, shadda, sukun, etc.)
_TAFSIR_DIACRITICS = re.compile(
    r'[\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8'
    r'\u06EA-\u06ED\u0610-\u061A\u08D3-\u08E1\u08E3-\u08FF'
    r'\u0640\u06E5\u06E6\u0653-\u0655\uFB50-\uFDFF\uFE70-\uFEFF]'
)


def _strip_arabic_diacritics(text: str) -> str:
    """Remove Arabic diacritics and normalize for matching."""
    text = _TAFSIR_DIACRITICS.sub('', text)
    text = text.replace('\u06E1', '')  # small high dotless head of khah
    text = text.replace('\u0657', '')  # inverted damma
    text = text.replace('\u065E', '')  # fatha with two dots
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا').replace('ٱ', 'ا')
    text = text.replace('\u0640', '')  # tatweel
    text = text.replace('\u200c', '').replace('\u200d', '')  # ZWJ/ZWNJ
    text = re.sub(r'[\u06D6-\u06DC\u06DF-\u06E4\u06E7\u06E8\u06EA-\u06ED]', '', text)
    text = re.sub(r'[\u0610-\u061A]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def _build_surah_map_stripped() -> dict[str, int]:
    stripped: dict[str, int] = {}
    for name, num in SURAH_MAP.items():
        s = _strip_arabic_diacritics(name)
        stripped[s] = num
        no_prefix = s.replace("سوره", "").replace("سورة", "").strip()
        if no_prefix:
            stripped[no_prefix] = num
    return stripped


_SURAH_MAP_STRIPPED = _build_surah_map_stripped()


def _parse_surah_number(surah_name: str) -> int:
    """Resolve Arabic surah name to its number (handles diacritics + prefix)."""
    if surah_name in SURAH_MAP:
        return SURAH_MAP[surah_name]
    stripped = _strip_arabic_diacritics(surah_name)
    if stripped in _SURAH_MAP_STRIPPED:
        return _SURAH_MAP_STRIPPED[stripped]
    no_prefix = stripped.replace("سوره", "").replace("سورة", "").strip()
    if no_prefix in _SURAH_MAP_STRIPPED:
        return _SURAH_MAP_STRIPPED[no_prefix]
    for name, num in _SURAH_MAP_STRIPPED.items():
        if no_prefix and no_prefix in name:
            return num
    return 0


def _parse_ayah_number(ayah_field: str) -> int:
    if not ayah_field:
        return 0
    stripped = ayah_field.strip()
    if stripped.isdigit():
        return int(stripped)
    m = _TAFSIR_AYAH_NUM_RE.search(stripped)
    if m:
        return int(m.group(1))
    return 0


def _match_priority(book_name: str, selected: set[str]) -> str | None:
    """Return priority tier (P0/P1/P2) if book_name matches, else None."""
    book_stripped = _strip_arabic_diacritics(book_name)
    for tier in ("P0", "P1", "P2"):
        if tier not in selected:
            continue
        for alternatives in PRIORITY_TAFSIRS[tier]:
            for pattern in alternatives:
                pattern_stripped = _strip_arabic_diacritics(pattern)
                if pattern_stripped in book_stripped or pattern in book_name:
                    return tier
    return None


def _build_tafsir_index_definition() -> dict[str, Any]:
    from al_furqan.kb.es.analyzers import ANALYSIS_SETTINGS  # pylint: disable=import-outside-toplevel
    return {
        "settings": {
            **ANALYSIS_SETTINGS,
            "number_of_shards": 1,
            "number_of_replicas": 0,
        },
        "mappings": {
            "properties": {
                "verse_key": {"type": "keyword"},
                "surah": {"type": "integer"},
                "ayah": {"type": "integer"},
                "tafsir_book": {"type": "keyword"},
                "priority": {"type": "keyword"},
                "content": {"type": "text", "analyzer": "arabic_furqan"},
                "content_length": {"type": "integer"},
            },
        },
    }


def _ingest_tafsirs(
    es,
    index: str,
    priorities: set[str],
    dry_run: bool,
    batch_size: int = 500,
) -> int:
    from datasets import load_dataset  # pylint: disable=import-outside-toplevel
    from elasticsearch.helpers import bulk  # pylint: disable=import-outside-toplevel

    logger.info("Downloading MohamedRashad/Quran-Tafseer from HuggingFace...")
    ds = load_dataset("MohamedRashad/Quran-Tafseer", split="train")
    logger.info("Downloaded %d rows", len(ds))

    all_books: set[str] = set(ds["tafsir_book"])
    matched_books: dict[str, str] = {}
    for book in all_books:
        tier = _match_priority(book, priorities)
        if tier is not None:
            matched_books[book] = tier

    logger.info("Matched %d tafsir books across tiers %s:",
                len(matched_books), sorted(priorities))
    for book, tier in sorted(matched_books.items(), key=lambda x: x[1]):
        logger.info("  [%s] %s", tier, book)

    if not matched_books:
        logger.error("No tafsir books matched the selected priorities. Use --list-books to inspect.")
        return 0

    if dry_run:
        book_counts: Counter[str] = Counter()
        for row in ds:
            if row["tafsir_book"] in matched_books:
                book_counts[row["tafsir_book"]] += 1
        total = sum(book_counts.values())
        logger.info("[DRY RUN] Would index %d entries:", total)
        for book, count in book_counts.most_common():
            logger.info("  %s: %d", book, count)
        return total

    if es.indices.exists(index=index):
        logger.warning("Deleting existing index: %s", index)
        es.indices.delete(index=index)

    logger.info("Creating index: %s", index)
    es.indices.create(index=index, body=_build_tafsir_index_definition())

    actions: list[dict[str, Any]] = []
    indexed = 0
    skipped = 0
    book_counter: Counter[str] = Counter()

    # The dataset's "ayah" field contains the verse TEXT, not always a number.
    # Track sequential ayah numbers per (book, surah) group.
    ayah_tracker: dict[tuple[str, int], int] = {}

    for row in ds:
        book_name: str = row["tafsir_book"]
        if book_name not in matched_books:
            continue

        surah = _parse_surah_number(row["surah_name"])
        if surah == 0:
            skipped += 1
            continue

        content: str = row["tafsir_content"]
        if not content or len(content.strip()) < 10:
            skipped += 1
            continue

        ayah = _parse_ayah_number(row["ayah"])
        if ayah == 0:
            key = (book_name, surah)
            prev = ayah_tracker.get(key, 0)
            ayah = prev + 1
            ayah_tracker[key] = ayah
        else:
            ayah_tracker[(book_name, surah)] = ayah

        verse_key = f"{surah}:{ayah}"
        tier = matched_books[book_name]
        doc_id = f"{verse_key}_{hash(book_name) % 100_000:05d}"

        actions.append({
            "_index": index,
            "_id": doc_id,
            "_source": {
                "verse_key": verse_key,
                "surah": surah,
                "ayah": ayah,
                "tafsir_book": book_name,
                "priority": tier,
                "content": content,
                "content_length": len(content),
            },
        })
        book_counter[book_name] += 1

        if len(actions) >= batch_size:
            success, errors = bulk(es, actions, raise_on_error=False)
            if errors:
                logger.warning("%d errors in batch", len(errors))
            indexed += success
            actions = []

    if actions:
        success, errors = bulk(es, actions, raise_on_error=False)
        if errors:
            logger.warning("%d errors in final batch", len(errors))
        indexed += success

    es.indices.refresh(index=index)

    logger.info("=" * 60)
    logger.info("Ingestion complete")
    logger.info("=" * 60)
    logger.info("  Books found:    %d", len(book_counter))
    logger.info("  Total indexed:  %d", indexed)
    logger.info("  Skipped:        %d", skipped)
    logger.info("  Entries per book:")
    for book, count in book_counter.most_common():
        tier = matched_books[book]
        logger.info("    [%s] %s: %d", tier, book, count)

    return indexed


def _list_tafsir_books() -> None:
    from datasets import load_dataset  # pylint: disable=import-outside-toplevel

    logger.info("Downloading MohamedRashad/Quran-Tafseer from HuggingFace...")
    ds = load_dataset("MohamedRashad/Quran-Tafseer", split="train")

    book_counts: Counter[str] = Counter()
    for row in ds:
        book_counts[row["tafsir_book"]] += 1

    logger.info("%s", "=" * 80)
    logger.info("Available tafsir books (%d total, %d rows)", len(book_counts), len(ds))
    logger.info("%s", "=" * 80)

    for i, (book, count) in enumerate(book_counts.most_common(), 1):
        tier = _match_priority(book, {"P0", "P1", "P2"})
        marker = f" <-- {tier}" if tier else ""
        logger.info("  %3d. [%5d] %s%s", i, count, book, marker)


def fetch_tafsirs(args: argparse.Namespace) -> None:
    from al_furqan.kb.es.client import create_es_client  # pylint: disable=import-outside-toplevel

    if args.list_books:
        _list_tafsir_books()
        return

    priorities: set[str]
    if args.priority == "all":
        priorities = {"P0", "P1", "P2"}
    else:
        priorities = {args.priority}

    hosts = [args.es_url] if args.es_url else None
    es = create_es_client(hosts=hosts)

    _ingest_tafsirs(
        es,
        index=args.index,
        priorities=priorities,
        dry_run=args.dry_run,
    )


def _add_tafsirs_parser(sub: argparse._SubParsersAction) -> None:
    p = sub.add_parser(
        "tafsirs",
        help="Ingest structural tafsirs from HuggingFace into Elasticsearch",
    )
    p.add_argument("--es-url", default=None,
                   help="Elasticsearch URL (default: http://localhost:9200)")
    p.add_argument("--index", default=TAFSIRS_DEFAULT_INDEX,
                   help=f"Index name (default: {TAFSIRS_DEFAULT_INDEX})")
    p.add_argument("--priority", default="all",
                   choices=["P0", "P1", "P2", "all"],
                   help="Priority tier to index (default: all)")
    p.add_argument("--dry-run", action="store_true",
                   help="Preview matching books and counts without indexing")
    p.add_argument("--list-books", action="store_true",
                   help="List all available tafsir_book names in the dataset and exit")
    p.set_defaults(func=fetch_tafsirs)


# ===========================================================================
# CLI dispatch
# ===========================================================================

def main() -> None:
    setup_logging()

    parser = argparse.ArgumentParser(
        description="Unified fetcher for Al-Furqan external data sources",
    )
    sub = parser.add_subparsers(dest="source", metavar="SOURCE", required=True)

    _add_wikipedia_parser(sub)
    _add_gutenberg_parser(sub)
    _add_youtube_parser(sub)
    _add_tafsirs_parser(sub)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
