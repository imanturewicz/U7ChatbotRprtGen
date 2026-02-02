import requests

class ConvocoreClient:
    def __init__(self, api_key, base_url="https://na-gcp-api.vg-stuff.com/v3"):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    # API call to fetch a single page of conversations
    def _fetch_page(self, agent_id, page, limit):
        url = f"{self.base_url}/agents/{agent_id}/convos"
        params = {"page": page, "limit": limit}
        try:
            r = requests.get(url, headers=self.headers, params=params)
            r.raise_for_status()
            return r.json().get("data", [])
        except Exception as e:
            print(f"❌ [Convocore] Error on page {page}: {e}")
            return []

    def fetch_conversations_generator(self, agent_id, batch_size=100):
        """Yields conversations one-by-one, handling pagination automatically."""
        page = 1
        while True:
            batch = self._fetch_page(agent_id, page, batch_size)
            if not batch:
                break
            for convo in batch:
                yield convo
            page += 1

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
    return count