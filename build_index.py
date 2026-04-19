import os
import json
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

DATA_FOLDER = "processed_json"
DB_PATH = "vector_store"

embedding = OpenAIEmbeddings(model="text-embedding-3-small")


def load_documents():
    docs = []

    for file in os.listdir(DATA_FOLDER):
        if not file.endswith(".json"):
            continue

        with open(os.path.join(DATA_FOLDER, file), "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data:
            docs.append(Document(
                page_content=item["text"],
                metadata={
                    "act": item["act"],
                    "section_id": item["section_id"],
                    "section_title": item["section_title"]
                }
            ))

    return docs


def build_index():
    docs = load_documents()
    print(f"Loaded {len(docs)} sections")

    db = FAISS.from_documents(docs, embedding)
    db.save_local(DB_PATH)

    print("Vector DB created")


if __name__ == "__main__":
    build_index()