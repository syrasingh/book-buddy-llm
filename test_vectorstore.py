# test_vectorstore.py
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
vectorstore = FAISS.load_local(
    "vectorstore",
    embeddings,
    allow_dangerous_deserialization=True,
)

# Test a search
results = vectorstore.similarity_search("fantasy books", k=3)

print(f"\nFound {len(results)} results:\n")
for i, doc in enumerate(results, 1):
    print(f"Result {i}:")
    print(doc.page_content[:300])
    print("\n" + "="*50 + "\n")