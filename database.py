import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

supabase: Client = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_KEY"]
)


def save_note(author_name, author_slack_id, filename, raw_content, summary, topics, embedding):
    """Save a processed research note to Supabase."""
    data = {
        "author_name": author_name,
        "author_slack_id": author_slack_id,
        "filename": filename,
        "raw_content": raw_content,
        "summary": summary,
        "topics": topics,
        "embedding": embedding
    }
    result = supabase.table("research_notes").insert(data).execute()
    return result


def search_notes(query_embedding: list, match_count: int = 5) -> list:
    """
    Semantic search using pgvector cosine similarity.
    Returns top matching notes for the given query embedding.
    """
    result = supabase.rpc("match_notes", {
        "query_embedding": query_embedding,
        "match_threshold": 0.4,  # Lower = more results, higher = stricter match
        "match_count": match_count
    }).execute()
    return result.data if result.data else []


def get_all_topics() -> list:
    """Get a flat list of all unique topics across all notes."""
    result = supabase.table("research_notes").select("topics").execute()
    all_topics = []
    for row in result.data:
        if row["topics"]:
            all_topics.extend(row["topics"])
    # Return unique topics sorted by frequency
    from collections import Counter
    counter = Counter(all_topics)
    return [topic for topic, _ in counter.most_common()]


def get_stats() -> dict:
    """Get overall stats: total notes, unique contributors."""
    result = supabase.table("research_notes").select("author_name").execute()
    total = len(result.data)
    contributors = list(set(row["author_name"] for row in result.data))
    return {
        "total_notes": total,
        "contributors": contributors
    }
