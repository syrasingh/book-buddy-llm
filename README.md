# 📚 Book Buddy — LLM-Powered Reading Recommendation Engine

Book Buddy is an end-to-end LLM-powered book recommendation app that generates personalized reading lists based on a user’s preferences (genre, mood, pace, length, and tropes). It uses retrieval-augmented generation (RAG) over real book summaries and reviews, and presents results through an interactive Streamlit interface.

## What This Project Does

- Scrapes real book data (titles + descriptions) from Goodreads pages
- Embeds and stores book content in a FAISS vectorstore
- Uses an LLM with retrieval to recommend books grounded in the scraped data
- Returns structured outputs (5-book reading lists with explanations)
- Estimates reading time based on page count heuristics
- Interactive Streamlit UI with preference controls and chat history

## Key ML / LLM Concepts Used

- Retrieval-Augmented Generation (RAG)
- Vector embeddings (OpenAI embeddings)
- FAISS similarity search
- Prompt engineering for structured output
- Tool-style post-processing (reading time estimation)
- Separation of data prep, backend logic, and UI

## Project Structure

```text
project/
├── backend.py            # LLM + retrieval logic
├── frontend.py           # Streamlit UI
├── prep_vectorstore.py   # Scrapes data & builds FAISS vectorstore
├── test_vectorstore.py   # Sanity check for retrieval
├── vectorstore/          # Generated FAISS index (local only)
├── requirements.txt      # Python dependencies
├── setup.sh              # One-command setup helper
├── README.md             # Project documentation
├── .env                  # API keys (NOT committed)
└── venv/                 # Local virtual environment (NOT committed)
```
**Note:** `vectorstore/`, `venv/`, and `.env` are intentionally excluded from version control.

## How the Pipeline Works (High Level)

### Data Collection
`prep_vectorstore.py` scrapes selected Goodreads book pages and extracts titles and descriptions.

### Chunking + Embedding
The text is split into chunks and embedded using OpenAI embeddings.

### Vector Storage
Embeddings are stored locally in a FAISS vectorstore for fast similarity search.

### Retrieval + Generation
At query time, the app retrieves relevant book chunks and passes them to the LLM to generate recommendations.

### Frontend Rendering
The Streamlit UI displays a structured 5-book reading list with explanations and estimated reading times.

## Running the Project Locally

### 1. Clone the repository
```text
git clone https://github.com/YOUR_USERNAME/book-buddy-llm.git
cd book-buddy-llm
```

### 2. Set up environment
```text
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Add API key
Create a `.env` file:
```text
OPENAI_API_KEY=your_api_key_here
```

### 4. Build the vectorstore
```text
python prep_vectorstore.py
```

### 5. Launch the app
```text
streamlit run frontend.py
```

## Design Decisions

- No vectorstore committed to ensure reproducibility
- Explicit RAG constraint to prevent hallucinations
- Structured outputs for clean UI rendering
- Lightweight heuristics for reading time estimation

## Future Improvements

- Add author metadata and genres to the vectorstore
- Improve Goodreads scraping robustness
- Add reranking or diversity constraints
- Deploy publicly (Streamlit Cloud or similar)

## Demo

