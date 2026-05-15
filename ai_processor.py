import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ["GROQ_API_KEY"])
MODEL = "llama-3.1-8b-instant"


def analyze_markdown(content: str) -> dict:
    """
    Sends the .md content to Groq/Llama and gets back:
    - summary: 2-3 sentence summary of key findings
    - topics: list of specific AI topics covered
    """
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
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
        max_tokens=500,
        temperature=0.3
    )

    text = response.choices[0].message.content.strip()

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
