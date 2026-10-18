import json
import os
import redis
import requests

def lambda_handler(event, context):
    try:
        # Initialize Redis client outside the handler to reuse connection across warm Lambda invocations
        REDIS_HOST = os.environ.get("REDIS_HOST", "f1-cache-aezpla.serverless.apse1.cache.amazonaws.com:6379")
        REDIS_PORT = int(os.environ.get("REDIS_PORT", 6379))
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

        redis_client.ping()

        BASE_URL = "https://api.openf1.org/v1"

        def get_latest_session_key_for_year(year):
            """
            Fetches all completed Race sessions for a given year and returns 
            the session_key of the final race.
            """
            params = {
                "session_name": "Race",
                "year": year
            }
            res = requests.get(f"{BASE_URL}/sessions", params=params)
            sessions = res.json()
            
            if not sessions:
                raise ValueError(f"No race sessions found for year {year}")
            
            # Sort by date_start to ensure we get the last Grand Prix of the season
            sessions.sort(key=lambda s: s.get("date_start", ""))
            last_race_session = sessions[-1]
            
            return last_race_session.get("session_key")

        def get_standings_for_year(year):
            cache_key = f"f1_standings_{year}"
            
            # 1. Check ElastiCache first
            cached_data = redis_client.get(cache_key)
            if cached_data:
                print(f"Cache hit for year {year}!")
                return json.loads(cached_data)
            
            print(f"Cache miss for year {year}. Resolving session key and fetching from OpenF1...")
            
            # 2. Resolve session key (use 'latest' shortcut for current season or look up final race)
            if year == "2026":
                session_key = "latest"
            else:
                session_key = get_latest_session_key_for_year(year)
            
            # 3. Fetch drivers and standings using the resolved session_key
            drivers_res = requests.get(f"{BASE_URL}/drivers", params={"session_key": session_key})
            drivers_map = {d["driver_number"]: d for d in drivers_res.json()}
            
            standings_res = requests.get(f"{BASE_URL}/championship_drivers", params={"session_key": session_key})
            standings_data = standings_res.json()
            
            # 4. Merge and format standings
            leaderboard = []
            for standing in standings_data:
                driver_num = standing.get("driver_number")
                driver_info = drivers_map.get(driver_num, {})
                
                first_name = driver_info.get("first_name") or ""
                last_name = driver_info.get("last_name") or ""
                
                merged_entry = {
                    "position": standing.get("position_current"),
                    "points": standing.get("points_current"),
                    "driver_number": driver_num,
                    "full_name": f"{first_name} {last_name}".strip(),
                    "name_acronym": driver_info.get("name_acronym"),
                    "team_name": driver_info.get("team_name"),
                    "team_colour": driver_info.get("team_colour"),
                    "headshot_url": driver_info.get("headshot_url")
                }
                leaderboard.append(merged_entry)
                
            leaderboard.sort(key=lambda x: x["position"] if x["position"] is not None else 999)
            
            # 5. Store in ElastiCache (Permanent for past years, 1-hour TTL for current season)
            if year != "2026":
                redis_client.set(cache_key, json.dumps(leaderboard))
            else:
                redis_client.setex(cache_key, 3600, json.dumps(leaderboard))
                
            return leaderboard

        query_params = event.get("queryStringParameters") or {}
        year = query_params.get("year", "2026")
        result = get_standings_for_year(year)

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(result)
        }

    except Exception as e:
        error_msg = str(e)
        tb = traceback.format_exc()
        print(f"CRITICAL ERROR: {error_msg}")
        print(tb)

        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": error_msg,
                "traceback": tb
            })
        }