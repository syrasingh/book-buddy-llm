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

# ----------------------------
# Tool: reading time estimate
# ----------------------------
def estimate_reading_time_hours(
    pages: Optional[int],
    wpm: int = 250,
    words_per_page: int = 275
) -> Optional[float]:
    if pages is None:
        return None
    minutes = (pages * words_per_page) / wpm
    return round(minutes / 60, 1)

def _normalize_pages(value) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        m = re.search(r"\d{2,4}", value)
        return int(m.group()) if m else None
    return None

# ----------------------------
# LLM: FORCE JSON OUTPUT
# NOTE: messages MUST contain the word "json" for response_format=json_object
# ----------------------------
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.4,
    api_key=os.getenv("OPENAI_API_KEY"),
    model_kwargs={"response_format": {"type": "json_object"}},
)

# ----------------------------
# Vectorstore + retriever
# ----------------------------
embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
vectorstore = FAISS.load_local(
    "vectorstore",
    embeddings,
    allow_dangerous_deserialization=True,
)
retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

def _format_context(docs) -> str:
    parts = []
    for d in docs:
        src = d.metadata.get("source", d.metadata.get("source_url", "unknown"))
        text = (d.page_content or "").strip()
        if not text:
            continue
        text = text[:1200]
        parts.append(f"Source: {src}\n{text}")
    return "\n\n---\n\n".join(parts)

# ----------------------------
# Main function used by Streamlit
# ----------------------------
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
            "error": "No context was retrieved from your vectorstore. Try rebuilding it (prep_vectorstore.py).",
            "raw": "",
        }

    # ---- Fix #2: Closest-match rules are explicitly in the instructions ----
    system = SystemMessage(content=f"""
You are a book recommendation assistant.

You must respond with valid json only. No extra text.

You must base recommendations on the retrieved context.
If the user's exact request (e.g., "funny romance") is not available, choose the closest matches from the retrieved books and explain why they’re the closest fit.

Return json exactly in this schema:
{{
  "reading_list": [
    {{
      "title": "string",
      "author": "string or null",
      "genre": "string or null",
      "why_it_matches": "1-2 sentences",
      "evidence_from_sources": "short signal from context",
      "estimated_pages": integer or null
    }}
  ],
  "follow_up_question": "string"
}}

Rules:
- Recommend exactly 5 books.
- If you can't find 5 perfect matches, still return 5 books that are the closest matches available in the retrieved context.
- Never say "I don't know."
- If author/genre/pages are unknown, use null.
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

Context (use this as your source):
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
            "error": "Model did not return valid JSON. Here is the raw output:",
            "raw": raw,
        }

    # 4) Validate/normalize
    reading_list = data.get("reading_list", [])
    if not isinstance(reading_list, list) or len(reading_list) == 0:
        return {
            "error": "JSON returned but reading_list is missing/empty. Raw output:",
            "raw": raw,
        }

    # Force exactly 5 (frontend expects 5)
    reading_list = reading_list[:5]
    while len(reading_list) < 5:
        reading_list.append({
            "title": None,
            "author": None,
            "genre": None,
            "why_it_matches": "Closest available match from the retrieved context.",
            "evidence_from_sources": None,
            "estimated_pages": None,
        })

    for item in reading_list:
        pages = _normalize_pages(item.get("estimated_pages"))
        item["estimated_pages"] = pages
        item["estimated_reading_time_hours"] = estimate_reading_time_hours(pages)

    data["reading_list"] = reading_list

    if not isinstance(data.get("follow_up_question"), str):
        data["follow_up_question"] = "Want me to refine by mood, length, or trope?"

    return data
