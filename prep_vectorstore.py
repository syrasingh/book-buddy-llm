# prep_vectorstore.py
import os
import time
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document  # ✅ add this

load_dotenv()

def scrape_goodreads_book(url):
    """Scrape specific parts of a Goodreads book page"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        }
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.content, "html.parser")

        title_tag = soup.find("h1")
        title = title_tag.get_text(strip=True) if title_tag else "Unknown"

        desc_tag = soup.find("div", {"data-testid": "description"})
        if not desc_tag:
            desc_tag = soup.find("span", class_="Formatted")

        description = desc_tag.get_text(" ", strip=True) if desc_tag else ""

        content = f"Title: {title}\n\nDescription: {description}"
        print(f"✓ Scraped: {title[:50]}...")
        return content

    except Exception as e:
        print(f"✗ Failed to scrape {url}: {e}")
        return None

# Your list of Goodreads book pages
WEBSITE_URLS = [
    "https://www.goodreads.com/book/show/5907.The_Hobbit",
    "https://www.goodreads.com/book/show/3.Harry_Potter_and_the_Sorcerer_s_Stone",
    "https://www.goodreads.com/book/show/45047384-the-house-in-the-cerulean-sea",
    "https://www.goodreads.com/book/show/186074.The_Name_of_the_Wind",
    "https://www.goodreads.com/book/show/8134945-mistborn",
    "https://www.goodreads.com/book/show/7235533-the-way-of-kings",
    "https://www.goodreads.com/book/show/1885.Pride_and_Prejudice",
    "https://www.goodreads.com/book/show/136251.Harry_Potter_and_the_Deathly_Hallows",
    "https://www.goodreads.com/book/show/11.The_Martian",
    "https://www.goodreads.com/book/show/54493401-project-hail-mary",
    "https://www.goodreads.com/book/show/375802.Ender_s_Game",
    "https://www.goodreads.com/book/show/234225.Dune",
    "https://www.goodreads.com/book/show/386162.The_Hitchhiker_s_Guide_to_the_Galaxy",
    "https://www.goodreads.com/book/show/2429135.The_Girl_with_the_Dragon_Tattoo",
    "https://www.goodreads.com/book/show/19288043-gone-girl",
    "https://www.goodreads.com/book/show/16299.And_Then_There_Were_None",
    "https://www.goodreads.com/book/show/18007564-the-silent-patient",
    "https://www.goodreads.com/book/show/10964.Outlander",
    "https://www.goodreads.com/book/show/15931.The_Notebook",
    "https://www.goodreads.com/book/show/41150487-red-white-royal-blue",
    "https://www.goodreads.com/book/show/25883848-the-hating-game",
    "https://www.goodreads.com/book/show/2767052-the-hunger-games",
    "https://www.goodreads.com/book/show/960.The_Perks_of_Being_a_Wallflower",
    "https://www.goodreads.com/book/show/28954189-six-of-crows",
    "https://www.goodreads.com/book/show/5104.The_Fault_in_Our_Stars",
    "https://www.goodreads.com/book/show/4934.The_Great_Gatsby",
    "https://www.goodreads.com/book/show/2657.To_Kill_a_Mockingbird",
    "https://www.goodreads.com/book/show/5107.The_Catcher_in_the_Rye",
    "https://www.goodreads.com/book/show/77203.The_Kite_Runner",
    "https://www.goodreads.com/book/show/19063.The_Book_Thief",
    "https://www.goodreads.com/book/show/11588.The_Shining",
    "https://www.goodreads.com/book/show/17899948-mexican-gothic",
    "https://www.goodreads.com/book/show/89717.The_Haunting_of_Hill_House",
    "https://www.goodreads.com/book/show/23692271-sapiens",
    "https://www.goodreads.com/book/show/35133922-educated",
    "https://www.goodreads.com/book/show/40121378-atomic-habits",
]

BOOK_URLS = WEBSITE_URLS  # ✅ add this

print(f"Scraping {len(BOOK_URLS)} book pages...")
print("This will take 1-2 minutes...\n")

documents = []
for i, url in enumerate(BOOK_URLS, 1):
    print(f"[{i}/{len(BOOK_URLS)}] ", end="")
    content = scrape_goodreads_book(url)
    if content:
        doc = Document(page_content=content, metadata={"source": url})
        documents.append(doc)
    time.sleep(2)

print(f"\n✓ Successfully scraped {len(documents)}/{len(BOOK_URLS)} books")

if len(documents) == 0:
    print("\n❌ ERROR: No books were scraped!")
    print("Goodreads is likely blocking requests.")
    exit(1)

text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = text_splitter.split_documents(documents)

print(f"✓ Split into {len(chunks)} chunks")

embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
print("✓ Creating vectorstore...")
vectorstore = FAISS.from_documents(chunks, embeddings)
vectorstore.save_local("vectorstore")

print("\n✅ SUCCESS! Vectorstore created!")
