# import json
from datetime import datetime, timedelta, timezone
import os, hmac, base64, hashlib

from flask import Flask, render_template, request, redirect, jsonify, abort, Markup, make_response, session
from setup_db import get_latest_tokens, get_sleep_data, get_workout_data, init_db
from dotenv import load_dotenv
from logic import sync_all_data, refresh_access_token

load_dotenv()
app = Flask(__name__)
#CLIENT_ID = os.environ["CLIENT_ID"]      
CLIENT_ID = os.environ["CLIENT_ID"]  
REDIRECT_URI = "https://imhtp-dev.github.io/longevityx/redirect.html"
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
#WHOOP_CLIENT_SECRET = os.environ.get("WHOOP_CLIENT_SECRET", "PLACEHOLDER_SECRET")
WHOOP_CLIENT_SECRET = os.environ.get("WHOOP_CLIENT_SECRET", "PLACEHOLDER_SECRET")

if WHOOP_CLIENT_SECRET == "PLACEHOLDER_SECRET":
    app.logger.warning("WHOOP_CLIENT_SECRET non impostato: uso placeholder; "
                       "verifica firma DISABILITATA fino a quando non configuri il secret")


@app.route("/refresh", methods=["POST"])
def refresh():
    print("refreshing")
    success = refresh_access_token()
    if success:
        return "Token aggiornato", 200
    else:
        return "Errore: nessun token disponibile", 400

@app.route('/')
def home():
    tokens = get_latest_tokens()
    
    if tokens is None:
        html = '''
        <h1>Non sei connesso</h1>
        <p>Devi prima connettere Whoop tramite login.</p>
        '''
    else:
        print(tokens)

    try:
        ts = datetime.strptime(tokens["timestamp"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except (KeyError, ValueError):
        return 0  # Timestamp mancante o invalido → token considerato scaduto

    expires_in = tokens.get("expires_in", 0)
    expiry_time = ts + timedelta(seconds=expires_in)

    now = datetime.now(timezone.utc)
    seconds_left = (expiry_time - now).total_seconds()

    print(f"[DEBUG] Token scade alle: {expiry_time}, ora attuale: {now}, secondi rimanenti: {seconds_left}")

    seconds_left = max(0, seconds_left)

    html = '''
    <h1>Sei connesso a Whoop</h1>
    <button onclick="syncData()">Sync Data</button>
    <script>
    async function syncData() {
        try {
            const res = await fetch('/sync', { method: 'POST' });
            const data = await res.json();
            alert(data.message);
        } catch (err) {
            alert('Error syncing data');
        }
    }
    </script>
    
    <br><br>
    <a href="/sleep"><button>Vedi Dati Sonno</button></a>
    <a href="/workouts"><button>Vedi Dati Allenamenti</button></a>
    '''
    html+=f'''<p>Tempo rimanente Access Token: {seconds_left} secondi</p>'''
    

    if seconds_left < 500:
        html += '''
        <button onclick="refreshToken()">Aggiorna Token</button>
        <script>
        async function refreshToken() {
            await fetch('/refresh', { method: 'POST' });
            location.reload();
        }
        </script>
        '''

    return Markup(html)

@app.route('/sync', methods=['POST'])
def sync():
    try:
        print("[SYNC] trying hard")
        sync_all_data()  
        print("[SYNC] tried")
        return jsonify({"message": "Dati sincronizzati con successo!"})
    except Exception as e:
        return jsonify({"message": f"Errore durante la sincronizzazione: {str(e)}"}), 500

@app.route('/sleep')
def sleep_page():
    sleep_data = get_sleep_data()
    return render_template('sleep.html', sleeps=sleep_data)

@app.route('/workouts')
def workouts_page():
    workout_data = get_workout_data()
    for w in workout_data:
            try:
                start = datetime.fromisoformat(w['start'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(w['end'].replace('Z', '+00:00'))
                duration = (end - start).total_seconds() / 60  # minutes
                w['duration'] = round(duration, 1)
            except Exception:
                w['duration'] = 'N/A'

    return render_template('workout.html', workouts=workout_data)

def verify_signature(req):
    sig = req.headers.get("X-WHOOP-Signature", "")
    ts = req.headers.get("X-WHOOP-Signature-Timestamp", "")
    body = req.get_data()
    msg = ts.encode() + body
    h = hmac.new(WHOOP_CLIENT_SECRET.encode(), msg, hashlib.sha256).digest()
    return hmac.compare_digest(base64.b64encode(h).decode(), sig)

@app.route("/webhook/whoop", methods=["POST"])
def whoop_webhook():
    if not verify_signature(request):
        abort(400, "Invalid signature")
    data = request.json
    app.logger.info(f"Webhook received: {data}")
    return "", 204

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify(status="ok"), 200

if __name__ == "__main__":
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5000)

