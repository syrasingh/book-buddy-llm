# frontend.py
import streamlit as st
from backend import get_chatbot_response

st.title("Your Fav Book Buddy 📚")
st.markdown("Tell me what kind of books you are interested in and I'll generate 5 recommendations.")

# Preferences form 
with st.sidebar:
    st.header("Your Preferences")

    genre = st.selectbox(
        "Genre",
        ["Any", "Fantasy", "Romance", "Mystery/Thriller", "Sci-Fi", "Literary", "Nonfiction", "YA"],
        index=0,
        key="genre_select"
    )
    mood = st.selectbox(
        "Mood",
        ["Any", "Cozy", "Dark", "Funny", "Emotional", "Inspirational", "Suspenseful", "Wholesome"],
        index=0,
        key="mood_select"
    )
    pace = st.selectbox(
        "Pace",
        ["Any", "Fast-paced", "Medium", "Slow-burn"],
        index=0,
        key="pace_select"
    )
    length_pref = st.selectbox(
        "Preferred length",
        ["Any", "Short (<250 pages)", "Medium (250–450)", "Long (450+)"],
        index=0,
        key="length_select"
    )
    
    # Get Recommendations button
    get_recs_button = st.button("Get Recommendations", use_container_width=True)

# Store preferences in session state so they persist
if "current_prefs" not in st.session_state:
    st.session_state.current_prefs = {
        "genre": "Any",
        "mood": "Any",
        "pace": "Any",
        "length_pref": "Any",
    }

# Update preferences whenever they change
st.session_state.current_prefs = {
    "genre": genre,
    "mood": mood,
    "pace": pace,
    "length_pref": length_pref,
}

# Chat history 
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize flag for button click processing
if "pending_button_prompt" not in st.session_state:
    st.session_state.pending_button_prompt = None

# Display existing chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Handle Get Recommendations button 
if get_recs_button:
    # Create a generic prompt based on preferences
    pref_parts = []
    if genre != "Any":
        pref_parts.append(f"{genre} books")
    if mood != "Any":
        pref_parts.append(f"with a {mood.lower()} mood")
    if pace != "Any":
        pref_parts.append(f"that are {pace.lower()}")
    if length_pref != "Any":
        pref_parts.append(f"({length_pref.lower()})")
    
    if pref_parts:
        auto_prompt = f"Recommend me {' '.join(pref_parts)}"
    else:
        auto_prompt = "Recommend me some great books"
    
    # Store the prompt to process on next run
    st.session_state.pending_button_prompt = auto_prompt
    st.rerun()

# Handle chat input
prompt = st.chat_input("What are you in the mood to read? (e.g., 'cozy fantasy like The Hobbit')")

# Determine which prompt to process
current_prompt = None

# Check if we have a pending button prompt
if st.session_state.pending_button_prompt:
    current_prompt = st.session_state.pending_button_prompt
    st.session_state.pending_button_prompt = None  # Clear it
elif prompt:
    current_prompt = prompt

# Process the prompt if we have one
if current_prompt:
    # Add user message to history
    st.session_state.messages.append({"role": "user", "content": current_prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(current_prompt)

    # Get and display assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            data = get_chatbot_response(current_prompt, prefs=st.session_state.current_prefs)
       
        if "error" in data:
            st.error(data["error"])
            st.code(data.get("raw", ""), language="json")
            assistant_msg = "❌ Error generating recommendations."
        else:
            reading_list = data.get("reading_list", [])
            for i, book in enumerate(reading_list, start=1):
                title = book.get("title", "Unknown title")
                author = book.get("author")
                genre_out = book.get("genre")
                why = book.get("why_it_matches", "")
                vibe_comparison = book.get("vibe_comparison", "")
                pages = book.get("estimated_pages")
                hours = book.get("estimated_reading_time_hours")

                header = f"**{i}. {title}**"
                if author:
                    header += f" by *{author}*"
                st.markdown(header)

                meta_bits = []
                if genre_out:
                    meta_bits.append(f"📚 {genre_out}")
                if pages:
                    meta_bits.append(f"📖 {pages} pages")
                if hours is not None:
                    meta_bits.append(f"⏱️ ~{hours} hrs")
                if meta_bits:
                    st.caption(" • ".join(meta_bits))

                st.write(why)
                if vibe_comparison:
                    st.info(f"💡 {vibe_comparison}")
                st.divider()

            st.info(data.get("follow_up_question", "Want more like this?"))
            assistant_msg = "✅ Reading list generated above."

    # Save assistant message to history
    st.session_state.messages.append({"role": "assistant", "content": assistant_msg})
