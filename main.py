import os
import requests
from collections import Counter
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}


def save_note(author_name, author_slack_id, filename, raw_content, summary, topics):
    """Save a processed research note to Supabase via REST API."""
    data = {
        "author_name": author_name,
        "author_slack_id": author_slack_id,
        "filename": filename,
        "raw_content": raw_content,
        "summary": summary,
        "topics": topics
    }
    response = requests.post(
        f"{SUPABASE_URL}/rest/v1/research_notes",
        headers=HEADERS,
        json=data
    )
    response.raise_for_status()
    return response.json()


def search_notes(query_text: str, match_count: int = 5) -> list:
    """Full-text search using PostgreSQL tsvector via Supabase REST API."""
    # Use Supabase's built-in full-text search
    search_headers = {**HEADERS, "Prefer": ""}
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/research_notes",
        headers=search_headers,
        params={
            "select": "id,author_name,filename,summary,topics,created_at",
            "search_vector": f"fts.{query_text}",
            "limit": match_count,
            "order": "created_at.desc"
        }
    )
    response.raise_for_status()
    results = response.json()

    # Fallback: if fts returns nothing, do a simple ilike search on summary
    if not results:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/research_notes",
            headers=search_headers,
            params={
                "select": "id,author_name,filename,summary,topics,created_at",
                "summary": f"ilike.*{query_text}*",
                "limit": match_count
            }
        )
        response.raise_for_status()
        results = response.json()

    return results if results else []


def get_all_topics() -> list:
    """Get a flat list of all unique topics sorted by frequency."""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/research_notes?select=topics",
        headers=HEADERS
    )
    response.raise_for_status()
    all_topics = []
    for row in response.json():
        if row.get("topics"):
            all_topics.extend(row["topics"])
    counter = Counter(all_topics)
    return [topic for topic, _ in counter.most_common()]


def get_stats() -> dict:
    """Get total notes count and unique contributors."""
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/research_notes?select=author_name",
        headers=HEADERS
    )
    response.raise_for_status()
    data = response.json()
    contributors = list(set(row["author_name"] for row in data))
    return {
        "total_notes": len(data),
        "contributors": contributors
    }
