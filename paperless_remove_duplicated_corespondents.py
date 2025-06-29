import requests
import json
import argparse

PAPERLESS_API = "http://192.168.178.49:8000/api"
PAPERLESS_API_KEY = open('.api_token').read().replace("\n", "")
OLLAMA_API = "http://192.168.178.25:11434/api/generate"
OLLAMA_MODEL = "llama3.3"

def get_all_correspondents(limit, page):
    print("[INFO] Loading all correspondents from Paperless...")
    headers = {"Authorization": f"Token {PAPERLESS_API_KEY}"}
    correspondents = []
    url = f"{PAPERLESS_API}/correspondents/?ordering=name"
    if limit:
        url += f"&page={page}&page_size={limit}"
    while url:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        correspondents.extend(data.get('results', []))
        url = data.get('next')
        print(f"[INFO] Intermediate count: {len(correspondents)} correspondents loaded...")
        if limit:
            return correspondents
    print(f"[INFO] Total: {len(correspondents)} correspondents loaded.")
    return correspondents

def find_similar_correspondents(correspondents):
    print("[INFO] Sending correspondent list to Ollama for similarity analysis...")
    names = [c['name'] for c in correspondents]
    prompt = (
        "You are given a list of correspondent names from a document management system."
        " Some names may refer to the same entity (e.g., slight spelling variations, added suffixes)."
        " Your task is to group names that likely refer to the same person or organization."
        " Return the groups as a JSON array of arrays. Example: [[\"John Smith\", \"John Smith GmbH\"], [\"ACME Corp\", \"ACME Corporation\"]]."
        "\n\nIMPORTANT: The output must be a valid JSON list of lists, without ´´´json. Do not include any explanatory text or formatting. please doublecheck the plausibility of each group!\n\n"
        f"Names: {json.dumps(names)}"
    )

    response = requests.post(OLLAMA_API, json={
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": True
    }, stream=True)
    response.raise_for_status()

    print("[OLLAMA OUTPUT START]")
    full_result = ""
    for line in response.iter_lines():
        if line:
            decoded = line
            try:
                data = json.loads(decoded)
                chunk = data.get("response", "")
                full_result += chunk
                print(chunk, end='', flush=True)
            except json.JSONDecodeError:
                print("[WARN] Could not decode chunk:", decoded)
    print("\n[OLLAMA OUTPUT END]")

    try:
        groups = json.loads(full_result)
        print(f"\n[INFO] {len(groups)} similar groups detected.")
        return groups
    except json.JSONDecodeError:
        print("[ERROR] Failed to parse response:", full_result)
        return []

def unify_correspondents(correspondents, similar_groups, dryrun):
    print("[INFO] Starting merge of similar correspondents...")
    headers = {
        "Authorization": f"Token {PAPERLESS_API_KEY}",
        "Content-Type": "application/json"
    }
    name_to_id = {c['name']: c['id'] for c in correspondents}

    for group in similar_groups:
        if len(group) < 2:
            continue

        main_name = group[0]
        main_id = name_to_id.get(main_name)

        if main_id is None:
            print(f"[WARN] Main correspondent '{main_name}' not found, skipping group")
            continue

        for other_name in group[1:]:
            other_id = name_to_id.get(other_name)
            if other_id is None:
                print(f"[WARN] Correspondent '{other_name}' not found, skipping")
                continue

            print(f"[INFO] Reassigning documents from '{other_name}' to '{main_name}'...")
            docs_url = f"{PAPERLESS_API}/documents/?correspondent__id__in={other_id}"
            while docs_url:
                response = requests.get(docs_url, headers=headers)
                response.raise_for_status()
                docs_data = response.json()
                for doc in docs_data.get('results', []):
                    doc_id = doc['id']
                    print(f"    [OK] Document {doc_id} would be updated")
                    if not dryrun:
                        patch_url = f"{PAPERLESS_API}/documents/{doc_id}/"
                        patch_data = {"correspondent": main_id}
                        patch_response = requests.patch(patch_url, headers=headers, json=patch_data)
                        patch_response.raise_for_status()
                        print(f"    [OK] Document {doc_id} updated!")
                docs_url = docs_data.get('next')

            print(f"[INFO] Deleting correspondent '{other_name}'...")
            if not dryrun:
                del_url = f"{PAPERLESS_API}/correspondents/{other_id}/"
                del_response = requests.delete(del_url, headers=headers)
                if del_response.status_code == 204:
                    print(f"    [OK] '{other_name}' deleted")
                else:
                    print(f"    [ERROR] Could not delete '{other_name}': {del_response.status_code}")
            else:
                print(f"    [DRYRUN] '{other_name}' would be deleted")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dryrun", action="store_true", help="Simulate changes only")
    parser.add_argument("--limit", type=int, help="Limit the number of correspondents to fetch, alphabetically sorted")
    parser.add_argument("--page", type=int, help="Limit the number of the page to fetch, alphabetically sorted")
    args = parser.parse_args()

    print("[START] Similarity check for correspondents started...")
    correspondents = get_all_correspondents(limit=args.limit, page=args.page)
    similar_groups = find_similar_correspondents(correspondents)

    print("[RESULT] Similar groups found:")
    for group in similar_groups:
        print(" -", group)

    unify_correspondents(correspondents, similar_groups, dryrun=args.dryrun)
    print("[END] Processing complete.")

if __name__ == "__main__":
    main()

