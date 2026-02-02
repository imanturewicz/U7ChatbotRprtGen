import requests

class ConvocoreClient:
    def __init__(self, api_key, base_url):
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

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

    def fetch_conversations_generator(self, agent_id, batch_size=50):
        """Yields conversations one-by-one, handling pagination automatically."""
        page = 1
        while True:
            batch = self._fetch_page(agent_id, page, batch_size)
            if not batch:
                break # No more data from API
            
            for convo in batch:
                yield convo
            
            page += 1