import requests

# Konfiguration
BASE_URL = "http://192.168.178.49:8000/api"
TOKEN = open('.api_token').read().replace("\n", "")

HEADERS = {
    "Authorization": f"Token {TOKEN}",
    "Accept": "application/json"
}

def get_all_correspondents():
    url = f"{BASE_URL}/correspondents/"
    correspondents = []
    while url:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        correspondents.extend(data["results"])
        url = data["next"]
    return correspondents

def delete_correspondent(correspondent_id, name):
    url = f"{BASE_URL}/correspondents/{correspondent_id}/"
    response = requests.delete(url, headers=HEADERS)
    if response.status_code == 204:
        print(f"✅ Gelöscht: {name} (ID: {correspondent_id})")
    else:
        print(f"❌ Fehler beim Löschen von {name} (ID: {correspondent_id}) – Status: {response.status_code}")

def main():
    correspondents = get_all_correspondents()
    print(f"🔍 {len(correspondents)} Korrespondenten gefunden.")
    count_deleted = 0

    for c in correspondents:
        if c["document_count"] == 0:
            delete_correspondent(c["id"], c["name"])
            count_deleted += 1

    print(f"\n🎉 Insgesamt {count_deleted} nicht verlinkte Korrespondenten gelöscht.")

if __name__ == "__main__":
    main()

