import requests
import difflib
import re
import argparse
from spellchecker import SpellChecker
from Levenshtein import ratio as levenshtein_ratio

API_URL = "http://192.168.178.49:8000"
API_TOKEN = open('.api_token').read().replace("\n", "")

HEADERS = {
    "Authorization": f"Token {API_TOKEN}",
    "Content-Type": "application/json",
}

spell = SpellChecker(distance=1)

def normalize(p: str) -> str:
    return re.sub(r'\s+', ' ', p.strip().lower())

def correct_spelling(text: str) -> str:
    words = text.split()
    corrected = [spell.correction(word) if word.lower() in spell.unknown([word]) else word for word in words]
    return ' '.join(corrected)

def is_similar(p1, p2, threshold=0.95, use_levenshtein=False) -> bool:
    return levenshtein_ratio(p1, p2) >= threshold if use_levenshtein else difflib.SequenceMatcher(None, p1, p2).ratio() >= threshold

def clean_paragraphs(text: str) -> list[str]:
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = re.sub(r'\n{2,}', '\n\n', text)
    return [p.strip() for p in text.split('\n\n') if p.strip()]

def remove_duplicates(text, threshold=0.95, levenshtein=False, spellcheck=False, dry_run=False, show_duplicates=False):
    print("Original metadata:\n" + "-"*30)
    print(text) 
    paragraphs = clean_paragraphs(text)
    seen = []
    unique = []
    duplicates = []

    print(paragraphs)
    for para in paragraphs:
        para_clean = correct_spelling(para) if spellcheck else para
        norm = normalize(para_clean)
        if any(is_similar(norm, normalize(correct_spelling(s) if spellcheck else s), threshold, levenshtein) for s in seen):
            duplicates.append(para)
            continue
        seen.append(para)
        unique.append(para)

    if dry_run:
        print(f"\nTotal: {len(paragraphs)} | Unique: {len(unique)} | Duplicates: {len(duplicates)}")
        if show_duplicates:
            print("\nDuplicates:\n" + "-"*40)
            for idx, d in enumerate(duplicates, 1):
                print(f"\n[{idx}] {d}")
        return None
    return "\n\n".join(unique)

def get_all_documents():
    documents = []
    next_url = f"{API_URL}/api/documents/?page_size=100"
    while next_url:
        r = requests.get(next_url, headers=HEADERS)
        r.raise_for_status()
        data = r.json()
        documents.extend(data['results'])
        next_url = data['next']
    return documents

def update_metadata(doc_id, new_content):
    r = requests.patch(f"{API_URL}/api/documents/{doc_id}/", headers=HEADERS, json={
        "metadata": new_content
    })
    r.raise_for_status()
    print(f"✓ Updated document {doc_id}")

def process_all_documents(args):
    docs = get_all_documents()
    print(f"Fetched {len(docs)} documents.")

    for doc in docs:
        metadata = doc.get("content", "")
        if not metadata.strip():
            continue
        print(f"\nProcessing document {doc['id']}: {doc['title']}")
        cleaned = remove_duplicates(
            metadata,
            threshold=args.threshold,
            levenshtein=args.levenshtein,
            spellcheck=not args.no_spellcheck,
            dry_run=args.dry_run,
            show_duplicates=args.show_duplicates
        )
        if not args.dry_run and cleaned and cleaned != metadata:
            update_metadata(doc['id'], cleaned)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clean Paperless document metadata using fuzzy duplicate detection.")
    parser.add_argument("--threshold", type=float, default=0.95, help="Similarity threshold")
    parser.add_argument("--levenshtein", action="store_true", help="Use Levenshtein instead of difflib")
    parser.add_argument("--no-spellcheck", action="store_true", help="Disable spellcheck")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no API writes)")
    parser.add_argument("--show-duplicates", action="store_true", help="Show duplicate paragraphs in dry run")

    args = parser.parse_args()
    process_all_documents(args)

