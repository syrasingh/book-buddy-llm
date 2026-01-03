# frontend.py
import streamlit as st
from backend import get_chatbot_response

st.title("Your Fav Book Buddy 📚")
st.markdown("Tell me what kind of books you are interested in and I’ll generate 5 recommendations.")

# --- Preferences form ---
with st.sidebar:
    st.header("Your Preferences")

    genre = st.selectbox(
        "Genre",
        ["Any", "Fantasy", "Romance", "Mystery/Thriller", "Sci-Fi", "Literary", "Nonfiction", "YA"],
        index=0
    )
    mood = st.selectbox(
        "Mood",
        ["Any", "Cozy", "Dark", "Funny", "Emotional", "Inspirational", "Suspenseful", "Wholesome"],
        index=0
    )
    pace = st.selectbox(
        "Pace",
        ["Any", "Fast-paced", "Medium", "Slow-burn"],
        index=0
    )
    length_pref = st.selectbox(
        "Preferred length",
        ["Any", "Short (<250 pages)", "Medium (250–450)", "Long (450+)"],
        index=0
    )
    tropes = st.multiselect(
        "Tropes / tags (optional)",
        ["Found family", "Enemies to lovers", "Grumpy/sunshine", "Coming-of-age", "Magic school", "Heist", "Cozy mystery"],
        default=[]
    )

prefs = {
    "genre": genre,
    "mood": mood,
    "pace": pace,
    "length_pref": length_pref,
    "tropes": tropes,
}

# --- Chat history ---
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("What are you in the mood to read? (e.g., 'cozy fantasy like The Hobbit')")
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        data = get_chatbot_response(prompt, prefs=prefs)

        if "error" in data:
            st.error(data["error"])
            st.code(data.get("raw", ""), language="json")
        else:
            reading_list = data.get("reading_list", [])
            for i, book in enumerate(reading_list, start=1):
                title = book.get("title", "Unknown title")
                author = book.get("author")
                genre_out = book.get("genre")
                why = book.get("why_it_matches", "")
                evidence = book.get("evidence_from_sources", "")
                pages = book.get("estimated_pages")
                hours = book.get("estimated_reading_time_hours")

                header = f"**{i}. {title}**"
                if author:
                    header += f" — {author}"
                st.markdown(header)

                meta_bits = []
                if genre_out:
                    meta_bits.append(f"Genre: {genre_out}")
                if pages:
                    meta_bits.append(f"Pages: {pages}")
                if hours is not None:
                    meta_bits.append(f"Est. reading time: {hours} hrs")
                if meta_bits:
                    st.caption(" • ".join(meta_bits))

                st.write(why)
                if evidence:
                    st.caption(f"Source signal: {evidence}")

                st.divider()

            st.info(data.get("follow_up_question", "Want more like this?"))

    # Save a short assistant message into history (not the whole list)
    st.session_state.messages.append({"role": "assistant", "content": "✅ Reading list generated above."})
