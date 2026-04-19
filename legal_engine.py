from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import json
import re

DB_PATH = "vector_store"

embedding = OpenAIEmbeddings(model="text-embedding-3-small")
db = FAISS.load_local(DB_PATH, embedding, allow_dangerous_deserialization=True)

llm = ChatOpenAI(model="gpt-4.1-mini", temperature=0)

def reformulate_query(query):
    prompt = f"""
Rewrite this into a precise legal search query.

Rules:
- Keep meaning same
- Add legal terminology
- No hallucination

Query:
{query}

Rewritten:
"""
    return llm.invoke(prompt).content.strip()

def analyze_crime(query):
    prompt = f"""
You are a legal expert.

Extract:
1. Possible crime types
2. Key actions

Return JSON:
{{
  "crime_types": [],
  "keywords": []
}}

Scenario:
{query}
"""
    return llm.invoke(prompt).content

def retrieve(query, k=10):
    return db.similarity_search(query, k=k)

def rerank(query, docs, top_k=5):
    context = "\n\n".join([
        f"[{i}] {d.page_content}"
        for i, d in enumerate(docs)
    ])

    prompt = f"""
Select the most relevant documents.

Return ONLY JSON list of indices.

Query:
{query}

Documents:
{context}

Top {top_k}:
"""

    response = llm.invoke(prompt).content.strip()

    match = re.search(r"\[.*\]", response)
    if match:
        indices = json.loads(match.group())
        return [docs[i] for i in indices if i < len(docs)]

    return docs[:top_k]

def generate_legal_response(query, docs):
    context = "\n\n".join([
        f"{d.metadata['act']} | Section {d.metadata['section_id']}:\n{d.page_content}"
        for d in docs
    ])

    prompt = f"""
You are a legal expert.

...

Example:

Scenario:
A corrupt government official accepted a bribe...

Output:
{{
  "crime_type": ["Corruption", "Drug trafficking"],
  "applicable_laws": [
    {{
      "act": "Prevention_of_Corruption_Act",
      "section": "7",
      "description": "Public servant taking undue advantage",
      "justification": "The official accepted a bribe."
    }},
    {{
      "act": "NDPS_Act",
      "section": "21",
      "description": "Punishment for possession/trafficking of narcotic substances",
      "justification": "Illegal drug trafficking activity."
    }}
  ]
}}

...

Return STRICT JSON:

{{
  "crime_type": [],
  "applicable_laws": [
    {{
      "act": "",
      "section": "",
      "description": "",
      "justification": ""
    }}
  ]
}}

Scenario:
{query}

Legal Context:
{context}
"""

    return llm.invoke(prompt).content


def run_pipeline(query):
    print("\n🔍 Input:", query)

    # Step 1: Reformulation
    refined = reformulate_query(query)

    # Step 2: Crime understanding
    analysis = analyze_crime(query)

    enhanced_query = query + " " + refined + " " + analysis

    # Step 3: Retrieval
    docs = retrieve(enhanced_query, k=10)

    # Step 4: Rerank
    docs = rerank(query, docs, top_k=5)

    # Step 5: Legal reasoning
    result = generate_legal_response(query, docs)

    return result