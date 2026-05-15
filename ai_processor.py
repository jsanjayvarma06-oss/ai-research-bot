import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.0-flash")


def analyze_markdown(content: str) -> dict:
    """
    Sends the .md content to Gemini and gets back:
    - summary: 2-3 sentence summary of key findings
    - topics: list of specific AI topics covered
    """
    prompt = f"""You are analyzing a research note about AI written by a student for their paper.

Analyze this markdown content and return a JSON object with exactly these two fields:
- "summary": A 2-3 sentence summary of the key findings. Be specific and technical.
- "topics": A list of 3-6 specific AI topics covered (e.g., "transformer architecture", "RLHF", "attention mechanism", "fine-tuning", "RAG")

Return ONLY valid JSON. No markdown code blocks, no explanation, nothing else.

Content to analyze:
{content}"""

    response = model.generate_content(prompt)
    text = response.text.strip()

    # Clean up if Gemini wraps in markdown code blocks
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])  # Remove first and last line

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback if parsing fails
        return {
            "summary": "Could not parse summary. Please check the file format.",
            "topics": ["AI research"]
        }


def generate_embedding(text: str) -> list:
    """
    Generates a 768-dimensional embedding vector for semantic search.
    Used for both storing notes and searching.
    """
    result = genai.embed_content(
        model="models/text-embedding-004",
        content=text[:8000],  # Limit to avoid token issues
        task_type="retrieval_document"
    )
    return result["embedding"]
