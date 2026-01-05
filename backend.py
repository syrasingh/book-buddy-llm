# backend.py
import os
import json
import re
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.messages import SystemMessage, HumanMessage

load_dotenv()

# Tool: reading time estimate
def estimate_reading_time_hours(
    pages: Optional[int],
    wpm: int = 250,
    words_per_page: int = 275
) -> Optional[float]:
    """Calculate reading time from page count"""
    if pages is None or pages <= 0:
        return None
    minutes = (pages * words_per_page) / wpm
    return round(minutes / 60, 1)

def _extract_pages_from_text(text: str) -> Optional[int]:
    """Extract page count from text like 'Pages: 310' or '310 pages'"""
    if not text:
        return None
    
    # Look for "Pages: XXX" format (from our scraping)
    match = re.search(r'Pages:\s*(\d{2,4})', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Look for "XXX pages" format
    match = re.search(r'(\d{2,4})\s*pages', text, re.IGNORECASE)
    if match:
        num = int(match.group(1))
        if 50 <= num <= 2000:  # Sanity check
            return num
    
    return None

def _normalize_pages(value) -> Optional[int]:
    """Normalize page count from various formats"""
    if value is None:
        return None
    if isinstance(value, int):
        return value if 50 <= value <= 2000 else None
    if isinstance(value, str):
        return _extract_pages_from_text(value)
    return None

# LLM: FORCE JSON OUTPUT
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.4,
    api_key=os.getenv("OPENAI_API_KEY"),
    model_kwargs={"response_format": {"type": "json_object"}},
)

# Vectorstore + retriever
embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
vectorstore = FAISS.load_local(
    "vectorstore",
    embeddings,
    allow_dangerous_deserialization=True,
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

def _format_context(docs) -> str:
    """Format retrieved documents with page counts highlighted"""
    parts = []
    for d in docs:
        src = d.metadata.get("source", "unknown")
        pages_meta = d.metadata.get("pages")
        text = (d.page_content or "").strip()
        if not text:
            continue
        
        # Include page count in context if available
        page_note = f" [Pages: {pages_meta}]" if pages_meta else ""
        text = text[:1200]
        parts.append(f"Source: {src}{page_note}\n{text}")
    return "\n\n---\n\n".join(parts)

# Main function used by Streamlit
def get_chatbot_response(user_question: str, prefs: Dict[str, Any]) -> Dict[str, Any]:
    genre = prefs.get("genre", "Any")
    mood = prefs.get("mood", "Any")
    pace = prefs.get("pace", "Any")
    length_pref = prefs.get("length_pref", "Any")
    tropes = prefs.get("tropes", [])

    # 1) Retrieve relevant docs
    docs = retriever.invoke(user_question)
    context = _format_context(docs)

    if not context.strip():
        return {
            "error": "No context was retrieved from your vectorstore.",
            "raw": "",
        }

    system = SystemMessage(content=f"""
You are a book recommendation assistant.

You must respond with valid json only. No extra text.

You must base recommendations on the retrieved context.
If the user's exact request is not available, choose the closest matches and explain why.

IMPORTANT: When you see "Pages: XXX" in the context, include that exact number in your response.
                           
For each recommendation, explain:
1. HOW it matches their specific mood/genre/pace request
2. WHAT makes it unique or compelling
3. WHO might especially love it (e.g., "fans of X will appreciate Y")

Be specific and enthusiastic, not generic.
                           
Return json exactly in this schema:
{{
  "reading_list": [
    {{
      "title": "string",
      "author": "string or null",
      "genre": "string or null",
      "why_it_matches": "3-4 sentences that specifically address their request (mood, pace, genre) with concrete details from the book",
      "vibe_comparison": "Optional: 'If you loved [popular book], you'll enjoy [specific aspect]' or null",
      "estimated_pages": integer (extract from "Pages: XXX" in context) or null
    }}
  ],
  "follow_up_question": "string"
}}

Rules:
- Recommend exactly 5 books.
- Extract page counts from context when available (look for "Pages: XXX")
- If you can't find 5 perfect matches, return 5 closest matches.
- Make explanations SPECIFIC to the user's request
- Use enthusiastic but honest language
- If author/genre/pages unknown, use null.
""".strip())

    mood_guide = """
Mood interpretation guide:
- Cozy: comforting, warm, low-stakes
- Dark: heavier themes, intense tone
- Funny: witty banter, humorous tone, rom-com energy
- Emotional: tearjerker / deep feelings
- Inspirational: uplifting, growth
- Suspenseful: tension, mystery, page-turner
- Wholesome: feel-good, kind characters
- Any: no mood constraint
""".strip()

    human = HumanMessage(content=f"""
User question: {user_question}

User preferences:
- Genre: {genre}
- Mood: {mood}
- Pace: {pace}
- Preferred length: {length_pref}
- Tropes/tags: {", ".join(tropes) if tropes else "None"}

{mood_guide}

Context (use this as your source - pay attention to "Pages: XXX"):
{context}

Reminder: output json only.
""".strip())

    # 2) Call model
    resp = llm.invoke([system, human])
    raw = resp.content

    # 3) Parse JSON
    try:
        data = json.loads(raw)
    except Exception:
        return {
            "error": "Model did not return valid JSON.",
            "raw": raw,
        }

    # 4) Validate and calculate reading times
    reading_list = data.get("reading_list", [])
    if not isinstance(reading_list, list) or len(reading_list) == 0:
        return {
            "error": "JSON returned but reading_list is missing/empty.",
            "raw": raw,
        }

    # Force exactly 5
    reading_list = reading_list[:5]
    while len(reading_list) < 5:
        reading_list.append({
            "title": None,
            "author": None,
            "genre": None,
            "why_it_matches": "Closest available match.",
            "evidence_from_sources": None,
            "estimated_pages": None,
        })

    for item in reading_list:
        # Try to get pages from the model's response or extract from context
        pages = _normalize_pages(item.get("estimated_pages"))
        
        # If model didn't provide pages, try to extract from evidence
        if not pages and item.get("evidence_from_sources"):
            pages = _extract_pages_from_text(item["evidence_from_sources"])
        
        # Calculate reading time using the scraped page count
        item["estimated_pages"] = pages
        item["estimated_reading_time_hours"] = estimate_reading_time_hours(pages)

    data["reading_list"] = reading_list

    if not isinstance(data.get("follow_up_question"), str):
        data["follow_up_question"] = "Want me to refine by mood, length, or trope?"

    return data
