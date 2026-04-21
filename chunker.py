import os
import json
from pathlib import Path
from collections import defaultdict

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from unstructured.partition.pdf import partition_pdf
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import ChatOpenAI

load_dotenv()

# =========================
# CONFIG
# =========================
PDF_FOLDER = "legal_pdfs"
OUTPUT_FOLDER = "processed_json"

MODEL = "gpt-4.1-mini"
CHUNK_SIZE = 20000
CHUNK_OVERLAP = 0

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# =========================
# STRUCTURED OUTPUT SCHEMA
# =========================
class SectionItem(BaseModel):
    section_id: str
    section_title: str = ""
    text: str = ""


class ChunkSections(BaseModel):
    sections: list[SectionItem] = Field(default_factory=list)


# =========================
# INIT LLM
# =========================
llm = ChatOpenAI(
    model=MODEL,
    temperature=0
)

structured_llm = llm.with_structured_output(ChunkSections)

# =========================
# PDF PROCESSING
# =========================
def pdf_to_elements(pdf_path):
    return partition_pdf(filename=pdf_path, strategy="fast")


def elements_to_text(elements):
    return "\n".join(
        el.text for el in elements if hasattr(el, "text") and el.text
    )

# =========================
# CHUNKING
# =========================
def split_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
    )
    return splitter.split_text(text)

# =========================
# EXTRACTION
# =========================
def extract_sections(chunk):
    prompt = f"""
Extract all legal sections from the text.

Rules:
- Do NOT hallucinate
- Keep exact section identifiers (e.g., Section 378)
- Include subsections like (1), (a), etc.
- If no sections found, return empty list

Return JSON:
{{
  "sections": [
    {{
      "section_id": "Section 378",
      "section_title": "Theft",
      "text": "full section text"
    }}
  ]
}}

TEXT:
\"\"\"{chunk}\"\"\"
"""

    try:
        result = structured_llm.invoke(prompt)
        return result.sections
    except Exception as e:
        print("Extraction error:", e)
        return []

# =========================
# MERGE
# =========================
def merge_sections(all_sections, act_name):
    merged = defaultdict(lambda: {
        "section_title": "",
        "texts": [],
        "seen": set()
    })

    for section_list in all_sections:
        for sec in section_list:
            sid = sec["section_id"].strip()
            if not sid:
                continue

            title = sec["section_title"].strip()
            text = sec["text"].strip()

            if title and not merged[sid]["section_title"]:
                merged[sid]["section_title"] = title

            if text:
                normalized = " ".join(text.split())
                if normalized not in merged[sid]["seen"]:
                    merged[sid]["texts"].append(text)
                    merged[sid]["seen"].add(normalized)

    return [
        {
            "act": act_name,
            "section_id": sid,
            "section_title": data["section_title"],
            "text": "\n\n".join(data["texts"]).strip(),
        }
        for sid, data in merged.items()
    ]

# =========================
# PROCESS PDF (WITH CHECKPOINT)
# =========================
def process_pdf(pdf_path):
    act_name = Path(pdf_path).stem
    print(f"\nProcessing: {act_name}")

    elements = pdf_to_elements(pdf_path)
    text = elements_to_text(elements)

    chunks = split_text(text)
    print(f"Total chunks: {len(chunks)}")

    temp_output_path = os.path.join(OUTPUT_FOLDER, f"{act_name}_temp.json")

    # Load checkpoint if exists
    if os.path.exists(temp_output_path):
        print("Resuming from checkpoint...")
        with open(temp_output_path, "r", encoding="utf-8") as f:
            all_sections = json.load(f)
    else:
        all_sections = []

    start_idx = len(all_sections)

    for i in range(start_idx, len(chunks)):
        print(f"Chunk {i+1}/{len(chunks)}")

        sections = extract_sections(chunks[i])

        # convert to dict before saving
        sections_dict = [s.dict() for s in sections]
        all_sections.append(sections_dict)

        # save checkpoint
        with open(temp_output_path, "w", encoding="utf-8") as f:
            json.dump(all_sections, f)

    print("All chunks processed")

    merged = merge_sections(all_sections, act_name)

    output_path = os.path.join(OUTPUT_FOLDER, f"{act_name}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    # remove temp file after success
    os.remove(temp_output_path)

    print(f"Saved: {output_path}")
    print(f"Sections extracted: {len(merged)}")

# =========================
# MAIN
# =========================
def process_all_pdfs():
    files = sorted(f for f in os.listdir(PDF_FOLDER) if f.endswith(".pdf"))
    print(f"Found {len(files)} PDFs")

    for f in files:
        process_pdf(os.path.join(PDF_FOLDER, f))


if __name__ == "__main__":
    process_all_pdfs()
