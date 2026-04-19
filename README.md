# Legal Crime Analyzer - RAG-based Legal Assistant

A Retrieval-Augmented Generation (RAG) system that accepts natural language descriptions of crime scenarios, identifies applicable crime types, and retrieves relevant legal provisions with justifications.

---

## Overview

The system processes a free-text crime scenario through a multi-step pipeline: query reformulation, crime analysis, vector-based retrieval, reranking, and LLM-based legal reasoning. The output is a structured JSON containing identified crime types and applicable legal sections with descriptions and justifications.

Unlike naive chunking approaches, this system extracts and indexes legal documents at the section level, significantly improving retrieval precision for legal queries.

---

## Problem Statement Mapping

Input:
- Free-text crime scenario in natural language

Output:
- Identified crime categories
- Relevant legal sections with descriptions
- Justification for why each section applies to the given scenario

---

## System Architecture

```
User Input (crime scenario)
        |
        v
Query Reformulation (LLM)
        |
        v
Crime Analysis (LLM) -- extracts crime types and keywords
        |
        v
Enhanced Query = original + reformulated + analysis
        |
        v
Vector Retrieval (FAISS, top-k=10)
        |
        v
Reranking (LLM-based, top-k=5)
        |
        v
Legal Reasoning + Response Generation (LLM)
        |
        v
Structured JSON Output
```

---

## Project Structure

```
.
├── app.py                        # Streamlit frontend
├── main.py                       # CLI entry point
├── legal_engine.py               # Core RAG pipeline
├── build_index.py                # Builds FAISS vector store from processed JSON
├── unstructured_legal_chunker.py # Ingests legal PDFs and extracts sections
├── legal_pdfs/                   # Input folder for raw legal PDF documents
├── processed_json/               # Extracted and chunked legal sections (JSON)
└── vector_store/                 # FAISS index files
```

---

## Setup Instructions

### Prerequisites

- Python 3.9+
- OpenAI API key

### Installation

```bash
git clone <your-repo-url>
cd <repo-folder>
pip install -r requirements.txt
```

Set your OpenAI API key:

```bash
export OPENAI_API_KEY=your_key_here
```

### Step 1 - Prepare Legal Documents

Place legal PDF files inside the `legal_pdfs/` folder. Then run the chunker to extract and process sections:

```bash
python unstructured_legal_chunker.py
```

This will create per-act JSON files inside `processed_json/`.

### Step 2 - Build the Vector Index

```bash
python build_index.py
```

This creates the FAISS index in `vector_store/`.

### Step 3 - Run the Application

**Web UI (Streamlit):**

```bash
streamlit run app.py
```

**Command Line:**

```bash
python main.py
```

---

## Legal Corpus Supported

- Bharatiya Nyaya Sanhita, 2023
- Bharatiya Nagarik Suraksha Sanhita, 2023
- Bharatiya Sakshya Adhiniyam, 2023
- Indian Penal Code, 1860
- Code of Criminal Procedure, 1973
- Indian Evidence Act, 1872
- Information Technology Act, 2000
- Narcotic Drugs and Psychotropic Substances Act, 1985
- Prevention of Corruption Act, 1988
- Protection of Children from Sexual Offences Act, 2012
- Unlawful Activities (Prevention) Act, 1967
- Dowry Prohibition Act, 1961
- Juvenile Justice (Care and Protection of Children) Act, 2015
- Protection of Women from Domestic Violence Act, 2005
- Motor Vehicles Act, 1988
- Arms Act, 1959
- Prevention of Money Laundering Act, 2002

---

## Output Format

```json
{
  "crime_type": ["House-breaking by night", "Theft"],
  "applicable_laws": [
    {
      "act": "India_Penal_Code",
      "section": "457",
      "description": "Lurking house-trespass or house-breaking by night in order to commit an offence punishable with imprisonment.",
      "justification": "The accused broke into a house during nighttime, which satisfies the elements of house-breaking by night under this section."
    },
    {
      "act": "India_Penal_Code",
      "section": "378",
      "description": "Whoever intending to take dishonestly any moveable property out of the possession of any person without that person's consent moves that property is said to commit theft.",
      "justification": "The accused took valuables from the premises without the owner's consent, directly satisfying the definition of theft."
    }
  ]
}
```

---

## Design Decisions

- **Retrieval-Augmented Generation (RAG)**: Instead of relying solely on LLM knowledge, the system retrieves relevant legal sections and grounds responses in actual law text, reducing hallucinations.
- **Query Reformulation**: The user's raw input is rewritten into a legal search query before retrieval to improve embedding similarity with legal text.
- **Crime Analysis as Context Enrichment**: A separate LLM call extracts crime types and keywords which are appended to the query, making retrieval more targeted.
- **LLM-based Reranking**: After vector retrieval, a second LLM pass selects the most relevant documents before generation, reducing noise in the context window.
- **Structured Output with `with_structured_output`**: During PDF ingestion, LangChain's structured output is used to extract sections reliably without regex parsing.
- **Checkpoint Support in Chunker**: The PDF processing pipeline saves progress per chunk so it can resume if interrupted, useful for large legal documents.
- **Grounded Responses**: The system strictly restricts outputs to retrieved legal context, preventing hallucinated sections. All prompts explicitly instruct the LLM not to reference any act or section not present in the retrieved context.

---

## Assumptions

- Legal PDFs are text-selectable (not scanned images). The chunker uses the `fast` strategy from `unstructured`.
- Each PDF filename is treated as the act name (e.g., `IPC_1860.pdf` becomes the act identifier `IPC_1860`).
- The system uses OpenAI `gpt-4.1-mini` for all LLM calls and `text-embedding-3-small` for embeddings.
- FAISS is used as the vector store and is loaded entirely in memory at query time.

---

## Limitations

- Performance depends on quality of the PDF ingestion. Scanned or poorly formatted PDFs will degrade extraction accuracy.
- Reranking is done by the LLM itself, which adds latency and is not a dedicated cross-encoder model.
- The vector store is flat FAISS with no hybrid search. Keyword-based retrieval is not used, which may miss exact section number matches.
- No conversation history is maintained. Each query is treated independently.
- The system does not handle procedural queries (e.g., bail, jurisdiction) well since the focus is on substantive criminal law sections.

---

## Future Improvements

- Add hybrid search (BM25 + dense retrieval) for better recall on exact section references.
- Integrate a proper cross-encoder reranker instead of using the LLM for reranking.
- Add support for scanned PDFs using OCR.
- Maintain conversation context for multi-turn interactions.
- Add a feedback mechanism so users can flag incorrect legal suggestions.
- Expand output to include punishment details and case law references.

---

## Sample Test Cases

### Case 1
Input: A person broke into a house at night and stole valuables.
Expected: House-breaking by night, Theft

### Case 2
Input: A man sent threatening messages online and leaked private photos of a woman without consent.
Expected: Cyberstalking, Obscenity, IT Act violations

### Case 3
Input: A government official accepted a bribe to clear a building permit.
Expected: Corruption, Bribery under Prevention of Corruption Act

### Case 4
Input: A person was caught carrying heroin at an airport.
Expected: Possession of narcotic substance under NDPS Act

### Case 5
Input: A drunk driver ran a red light and injured a pedestrian.
Expected: Rash driving, causing hurt by negligence under Motor Vehicles Act and IPC

### Case 6
Input: A man repeatedly beat his wife and threatened to throw her out of the house.
Expected: Domestic violence, Cruelty

### Case 7
Input: A group of individuals raised funds for a terrorist organization.
Expected: Unlawful Activities under UAPA, Money Laundering under PMLA

### Case 8
Input: An adult man groomed and sexually assaulted a 14-year-old child.
Expected: POCSO Act offences, IPC provisions on sexual assault

---

## Built With

- LangChain
- OpenAI GPT-4.1-mini
- FAISS
- Streamlit
- Unstructured (PDF parsing)
