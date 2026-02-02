import requests
import json

def get_voiceflow_users(api_key, project_id, start_date, end_date):
    url = "https://analytics-api.voiceflow.com/v2/query/usage"
    
    # Format dates for Voiceflow (ISO 8601)
    # e.g., "2026-01-01T00:00:00.000Z"
    fmt = "%Y-%m-%dT%H:%M:%S.000Z"
    start_str = start_date.strftime(fmt)
    end_str = end_date.strftime(fmt)
    
    headers = {
        "accept": "application/json",
        "authorization": api_key,
        "content-type": "application/json"
    }

    all_items = []
    next_cursor = None
    MAX_LOOPS = 10 # Safety brake
    
    print(f"📊 [Voiceflow] Fetching from {start_str} to {end_str}...")

    for i in range(MAX_LOOPS):
        payload = {
            "data": {
                "name": "unique_users",
                "filter": {
                    "projectID": project_id,
                    "limit": 500,
                    "startTime": start_str,
                    "endTime": end_str
                }
            }
        }

        if next_cursor:
            payload["data"]["filter"]["cursor"] = next_cursor

        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            result = response.json().get("result", {})
            items = result.get("items", [])
            
            if not items:
                break

            # Infinite Loop Check
            if len(all_items) > 0 and items[0].get('period') == all_items[0].get('period'):
                print("⚠️ [Voiceflow] Loop detected. Stopping.")
                break

            all_items.extend(items)
            next_cursor = result.get("cursor")
            
            if not next_cursor:
                break
                
        except Exception as e:
            print(f"❌ [Voiceflow] Error: {e}")
            break

    total = sum(item['count'] for item in all_items)
    return total