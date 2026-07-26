import time

import requests

class ConvocoreClient:
    def __init__(self, api_key, base_url="https://eu-gcp-api.vg-stuff.com/v3"): #https://na-gcp-api.vg-stuff.com/v3 for NA
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    # API call to fetch a single page of conversations
    def _fetch_page(self, agent_id, limit, cursor=None):
        time.sleep(10)  # Sleep for 10 seconds to avoid rate limiting
        url = f"{self.base_url}/agents/{agent_id}/convos"
        params = {"limit": limit}
        
        if cursor:
            params["cursor"] = cursor
            
        try:
            r = requests.get(url, headers=self.headers, params=params)
            r.raise_for_status()
            response_json = r.json()
            
            # Pobranie danych
            data = response_json.get("data", [])
            
            # FIX: Zmiana klucza na camelCase zgodnie z odpowiedzą serwera
            next_cursor = response_json.get("nextCursor") 
            
            return data, next_cursor
            
        except Exception as e:
            print(f"❌ [Convocore] Błąd komunikacji (cursor: {cursor}): {e}")
            return [], None

    def fetch_conversations_generator(self, agent_id, batch_size=20):
        """Yields conversations one-by-one, handling cursor-based pagination."""
        current_cursor = None
        
        while True:
            # Rozpakowanie zwracanej krotki (dane, nowy kursor)
            batch, next_cursor = self._fetch_page(agent_id, limit=batch_size, cursor=current_cursor)
            
            if not batch:
                break
                
            for convo in batch:
                yield convo
                
            # Jeśli API nie zwraca kolejnego kursora, przerywamy pętlę
            if not next_cursor:
                break
                
            # Aktualizacja kursora do następnego wywołania
            current_cursor = next_cursor

def getConvocoreTagsNo(api_key, agent_id, start_date, end_date, target_tag):
    """
    Counts how many conversations in the date range have the specific tag.
    """
    print(f"📊 [Convocore] Counting tag '{target_tag}'...")
    
    # 1. Setup
    client = ConvocoreClient(api_key)
    start_ts = start_date.timestamp()
    end_ts = end_date.timestamp()
    
    count = 0
    checked_convos = 0

    # 2. Iterate (Newest -> Oldest)
    for convo in client.fetch_conversations_generator(agent_id):
        ts = convo.get("ts", 0)

        # A. Too New (Future) -> Skip
        if ts >= end_ts:
            continue
            
        # B. Too Old (Past) -> Stop
        if ts < start_ts:
            break
            
        # C. Target Range -> Check Tags
        tags = convo.get("tags", [])
        if target_tag in tags:
            count += 1
            
        checked_convos += 1

    print(f"   -> Found {count} occurrences in {checked_convos} conversations.")
    return count, checked_convos