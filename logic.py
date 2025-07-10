import os
from setup_db import insert_sleep, get_latest_tokens, insert_workout, save_tokens
import requests 
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone



load_dotenv()
CLIENT_ID = os.environ["CLIENT_ID"]  
REDIRECT_URI = "https://imhtp-dev.github.io/longevityx/redirect.html"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
WHOOP_CLIENT_SECRET = os.environ.get("WHOOP_CLIENT_SECRET", "PLACEHOLDER_SECRET")


def refresh_access_token():
    tokens = get_latest_tokens()
    if not tokens:
        print("[ERR] Nessun refresh token salvato.")
        return

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": tokens["refresh_token"],
        "client_id": {CLIENT_ID},
        "client_secret": {WHOOP_CLIENT_SECRET},
    }

    r = requests.post(TOKEN_URL, data=payload)
    r.raise_for_status()

    new_tokens = r.json()
    access_token = new_tokens["access_token"]
    refresh_token = new_tokens["refresh_token"]
    expires_in = new_tokens.get("expires_in", 0)

    save_tokens(access_token, refresh_token, expires_in)
    print(f"[+] Access Token aggiornato e salvato nel DB.")

def sync_all_data():
    header = make_header()
    print("[HEADER]" + str(header))
    fetch_and_insert_sleep(header)
    fetch_and_insert_workouts(header)
    print("[SYNC] Dati aggiornati.")


def make_header():
    token_data = get_latest_tokens()
    if not token_data or "access_token" not in token_data:
        raise Exception("Access token non trovato.")
    access_token = token_data["access_token"]
    return {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json"
    }



def fetch_and_insert_sleep(header, start=None, end=None):
    if not start:
        start = (datetime.now(timezone.utc) - timedelta(days=30)).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    print(start)

    url = "https://api.prod.whoop.com/developer/v1/activity/sleep"
    params = {"start": start, "end": end}
    r = requests.get(url, headers=header, params=params)

    next_token = None
    while True:
        if next_token:
            params["nextToken"] = next_token
        else:
            params.pop("nextToken", None)

        r = requests.get(url, headers=header, params=params)
        if r.status_code == 200:
            data = r.json()
            records = data.get("records", [])
            for sleep in records:
                print("[SLEEP]" + str(sleep))
                insert_sleep(sleep)
            print(f"[SLEEP] {len(records)} saved.")
            next_token = data.get("nextToken")
            if not next_token:
                break
        else:
            print(f"[ERROR] Fetch sleep: {r.status_code} - {r.text}")
            break


def fetch_and_insert_workouts(header, start=None, end=None):
    if not start:
        start = (datetime.now(timezone.utc) - timedelta(days=30)).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    print(start)

    url = "https://api.prod.whoop.com/developer/v1/activity/workout"
    params = {"start": start, "end": end}
    r = requests.get(url, headers=header, params=params)

    next_token = None
    while True:
        if next_token:
            params["nextToken"] = next_token
        else:
            params.pop("nextToken", None)

        r = requests.get(url, headers=header, params=params)
        if r.status_code == 200:
            data = r.json()
            records = data.get("records", [])
            for sleep in records:
                insert_workout(sleep)
            print(f"[SLEEP] {len(records)} saved.")
            next_token = data.get("nextToken")
            if not next_token:
                break
        else:
            print(f"[ERROR] Fetch sleep: {r.status_code} - {r.text}")
            break
