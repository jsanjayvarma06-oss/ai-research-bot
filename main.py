import os
import re
import urllib.request
import ssl
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
from ai_processor import analyze_markdown
from database import save_note, search_notes, get_all_topics, get_stats

load_dotenv()

app = App(token=os.environ["SLACK_BOT_TOKEN"])


# ─── FILE UPLOAD HANDLER ───────────────────────────────────────────────────────

@app.event({"type": "message", "subtype": "file_share"})
def handle_file_message(event, client, say):
    try:
        files = event.get("files", [])
        if not files:
            return

        user_id = event.get("user")
        user_info = client.users_info(user=user_id)
        author_name = user_info["user"]["real_name"]

        for file in files:
            if not file["name"].endswith(".md"):
                continue
            process_file(file, author_name, user_id, client, say)

    except Exception as e:
        say(f"❌ Something went wrong: `{str(e)}`")
        print(f"Error in handle_file_message: {e}")


@app.event("file_shared")
def handle_file_shared(event, client, say):
    try:
        file_id = event["file_id"]
        user_id = event.get("user_id")

        file_info = client.files_info(file=file_id)
        file = file_info["file"]

        if not file["name"].endswith(".md"):
            return

        user_info = client.users_info(user=user_id)
        author_name = user_info["user"]["real_name"]

        process_file(file, author_name, user_id, client, say)

    except Exception as e:
        say(f"❌ Something went wrong: `{str(e)}`")
        print(f"Error in handle_file_shared: {e}")


def process_file(file, author_name, user_id, client, say):
    say(f"📥 Got `{file['name']}` from *{author_name}*! Analyzing... hang tight ⏳")

    url = file["url_private_download"]
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {os.environ['SLACK_BOT_TOKEN']}"}
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, context=ctx) as response:
        content = response.read().decode("utf-8")

    analysis = analyze_markdown(content)

    save_note(
        author_name=author_name,
        author_slack_id=user_id,
        filename=file["name"],
        raw_content=content,
        summary=analysis["summary"],
        topics=analysis["topics"]
    )

    topics_str = "  •  ".join(analysis["topics"])
    say(
        f"✅ *Saved to the research brain!*\n\n"
        f"👤 *Author:* {author_name}\n"
        f"📄 *File:* `{file['name']}`\n"
        f"📝 *Summary:* {analysis['summary']}\n"
        f"🏷️ *Topics:* {topics_str}"
    )


# ─── QUERY HANDLER ────────────────────────────────────────────────────────────

@app.message(re.compile(r"^(query|search|find|what do we know about)\s+(.+)", re.IGNORECASE))
def handle_query(message, say, context):
    try:
        query_text = context["matches"][1].strip()
        user_id = message["user"]
        user_info = app.client.users_info(user=user_id)
        requester = user_info["user"]["real_name"]

        say(f"🔍 *{requester}* is searching for: *{query_text}*...")

        # Search using full-text search
        results = search_notes(query_text, match_count=5)

        if not results:
            say(
                f"😕 No relevant notes found for *{query_text}* yet.\n"
                f"Keep submitting those `.md` files and build up the brain! 🧠"
            )
            return

        response = f"📚 *Here's what the team knows about \"{query_text}\":*\n\n"
        for i, note in enumerate(results, 1):
            date = note["created_at"][:10]
            topics = "  •  ".join(note["topics"]) if note["topics"] else "N/A"
            response += (
                f"*{i}. {note['author_name']}* — `{note['filename']}` _{date}_\n"
                f"   {note['summary']}\n"
                f"   🏷️ {topics}\n\n"
            )

        say(response)

    except Exception as e:
        say(f"❌ Search failed: `{str(e)}`")
        print(f"Error in handle_query: {e}")


# ─── STATS HANDLER ────────────────────────────────────────────────────────────

@app.message("!stats")
def handle_stats(message, say):
    try:
        stats = get_stats()
        topics = get_all_topics()
        top_topics = ", ".join(topics[:10]) if topics else "None yet"

        say(
            f"📊 *Research Brain Stats*\n\n"
            f"📄 Total notes submitted: *{stats['total_notes']}*\n"
            f"👥 Contributors: *{', '.join(stats['contributors']) if stats['contributors'] else 'None yet'}*\n"
            f"🏷️ Top topics explored: {top_topics}"
        )
    except Exception as e:
        say(f"❌ Couldn't fetch stats: `{str(e)}`")


# ─── HELP HANDLER ─────────────────────────────────────────────────────────────

@app.message("!help")
def handle_help(message, say):
    say(
        "👋 *AI Research Brain — Commands:*\n\n"
        "📤 *Submit notes:* Upload a `.md` file in this channel\n"
        "   → I'll analyze it, tag topics, and save it with your name\n\n"
        "🔍 *Search:* `query <topic>` or `search <topic>`\n"
        "   Example: `query transformer architecture`\n"
        "   Example: `search reinforcement learning`\n\n"
        "📊 *Stats:* `!stats` — see how many notes and who contributed\n\n"
        "❓ *Help:* `!help` — show this message"
    )


# ─── START ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🚀 AI Research Bot is starting...")
    handler = SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"])
    handler.start()
