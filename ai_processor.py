import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.1-8b-instant"

HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}


def analyze_markdown(content: str) -> dict:
    """
    Sends the .md content to Groq/Llama and gets back:
    - summary: 2-3 sentence summary of key findings
    - topics: list of specific AI topics covered
    """
    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are analyzing research notes about AI written by students. "
                    "Always respond with valid JSON only. No markdown, no explanation, nothing else."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Analyze this markdown content and return a JSON object with exactly:\n"
                    f"- \"summary\": A 2-3 sentence summary of the key findings (be specific and technical)\n"
                    f"- \"topics\": A list of 3-6 specific AI topics covered "
                    f"(e.g. \"transformer architecture\", \"RLHF\", \"attention mechanism\")\n\n"
                    f"Content:\n{content[:4000]}"
                )
            }
        ],
        "max_tokens": 500,
        "temperature": 0.3
    }

    response = requests.post(GROQ_URL, headers=HEADERS, json=payload)
    response.raise_for_status()

    text = response.json()["choices"][0]["message"]["content"].strip()

    # Clean up if model wraps in markdown code blocks
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "summary": "Could not parse summary. Please check the file format.",
            "topics": ["AI research"]
        }
