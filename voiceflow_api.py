import requests
import datetime

class VoiceflowClient:
    def __init__(self, api_key, project_id):
        self.api_key = api_key
        self.project_id = project_id
        # Note: Analytics V2 (users) and V1 (transcripts) use different base URLs usually,
        # so we will build the full URL inside each method to be safe.
        self.headers = {
            "accept": "application/json",
            "authorization": api_key,
            "content-type": "application/json"
        }
        self.fmt = "%Y-%m-%dT%H:%M:%S.000Z"
    
    def _format_to_utc_string(self, dt):
        return dt.astimezone(datetime.timezone.utc).strftime(self.fmt)

    def get_unique_users__or_interactions(self, start_date, end_date, metric="unique_users"):
        """
        Fetches unique user count or interaction count using Analytics API v2.
        """
        url = "https://analytics-api.voiceflow.com/v2/query/usage"
        
        # 1. Setup Loop
        all_items = []
        next_cursor = None
        MAX_LOOPS = 10 
        
        print(f"📊 [Voiceflow] Fetching {metric}...")

        for i in range(MAX_LOOPS):
            payload = {
                "data": {
                    "name": metric,
                    "filter": {
                        "projectID": self.project_id,
                        "limit": 500,
                        "startTime": self._format_to_utc_string(start_date),
                        "endTime": self._format_to_utc_string(end_date)
                    }
                }
            }

            if next_cursor:
                payload["data"]["filter"]["cursor"] = next_cursor

            try:
                response = requests.post(url, json=payload, headers=self.headers)
                response.raise_for_status()
                result = response.json().get("result", {})
                items = result.get("items", [])
                
                if not items:
                    break

                # Infinite Loop Safety Check
                if len(all_items) > 0 and items[0].get('period') == all_items[0].get('period'):
                    print("⚠️ [Voiceflow] Loop detected. Stopping.")
                    break

                all_items.extend(items)
                next_cursor = result.get("cursor")
                
                if not next_cursor:
                    break
                    
            except Exception as e:
                print(f"❌ [Voiceflow Users] Error: {e}")
                break

        total = sum(item['count'] for item in all_items)
        return total

    def fetch_transcripts(self, start_date, end_date, environment_id):
        """
        Generator that yields transcripts one by one.
        Handles pagination (take/skip) automatically.
        """
        base_url = f"https://analytics-api.voiceflow.com/v1/transcript/project/{self.project_id}"
        
        # Pagination settings
        take = 100
        skip = 0
        
        print(f"📝 [Voiceflow] Fetching transcripts ({start_date.date()} to {end_date.date()})...")

        while True:
            # 1. URL Params for Pagination
            params = {
                "take": take,
                "skip": skip,
                "order": "DESC" # Newest first
            }
            
            # 2. JSON Body for Filtering
            payload = {
                "startDate": self._format_to_utc_string(start_date),
                "endDate": self._format_to_utc_string(end_date),
                "environmentID": environment_id
            }

            try:
                # Note: 'params' go in the URL (?take=100), 'json' goes in the body
                response = requests.post(base_url, headers=self.headers, params=params, json=payload)
                response.raise_for_status()
                
                data = response.json()
                transcripts = data.get("transcripts", [])
                
                # STOP CONDITION: No more transcripts returned
                if not transcripts:
                    break

                # Yield transcripts from this batch
                for t in transcripts:
                    yield t

                # Increment Skip for next batch
                print(f"   -> Fetched batch: skip={skip} (Got {len(transcripts)} items)")
                skip += take

            except Exception as e:
                print(f"❌ [Voiceflow Transcripts] Error at skip {skip}: {e}")
                break

    def end_transcript(self, transcript_id):
        """
        Forcefully ends a specific transcript session.
        """
        # Construct URL: .../transcript/{id}/project/{projectID}/end
        url = f"https://analytics-api.voiceflow.com/v1/transcript/{transcript_id}/project/{self.project_id}/end"
        
        try:
            # POST request with no body, just headers
            response = requests.post(url, headers=self.headers)
            response.raise_for_status()
            print(f"   ✅ Ended transcript: {transcript_id}")
            return True
            
        except Exception as e:
            print(f"   ❌ Failed to end {transcript_id}: {e}")
            return False

def end_active_transcripts(vf_client, transcripts_list):
    """
    Iterates through a provided list of transcripts and ends 
    any that are still active.
    """
    print(f"🧹 [Cleanup] Scanning {len(transcripts_list)} transcripts in memory...")
    
    ended_count = 0
    
    for t in transcripts_list:
        t_id = t.get("id")
        ended_at = t.get("endedAt")
        
        # LOGIC: Check list in memory
        if not ended_at:
            # Action: Call API only when needed
            if vf_client.end_transcript(t_id):
                ended_count += 1
                
                # OPTIONAL: Update the list in memory so next steps know it's closed
                # t["endedAt"] = "just_now" 
    
    print(f"✅ Cleanup finished. Forcefully ended {ended_count} stale sessions.")
    return ended_count