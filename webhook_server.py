import os, hmac, base64, hashlib
from flask import Flask, request, abort, jsonify 

app = Flask(__name__)
CLIENT_ID     = os.environ["CLIENT_ID"]        
REDIRECT_URI  = "https://imhtp-dev.github.io/longevityx/redirect.html"
TOKEN_URL     = "https://api.prod.whoop.com/oauth/oauth2/token"
WHOOP_CLIENT_SECRET = os.environ.get("WHOOP_CLIENT_SECRET")
if not WHOOP_CLIENT_SECRET:
    WHOOP_CLIENT_SECRET = "PLACEHOLDER_SECRET"
    app.logger.warning("WHOOP_CLIENT_SECRET non impostato: uso placeholder; "
                       "verifica firma DISABILITATA fino a quando non configuri il secret")


'''WHOOP_CLIENT_SECRET = os.environ.get("WHOOP_CLIENT_SECRET")
if not WHOOP_CLIENT_SECRET:
    raise RuntimeError("Set WHOOP_CLIENT_SECRET env var")'''

def verify_signature(req):
    sig = req.headers.get("X-WHOOP-Signature", "")
    ts  = req.headers.get("X-WHOOP-Signature-Timestamp", "")
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
@app.post("/oauth/exchange")
def oauth_exchange():
    payload = request.get_json()
    code  = payload["code"]
    state = payload["state"]                     

    data = {
        "grant_type":    "authorization_code",
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
        "client_id":     CLIENT_ID,
        "client_secret": WHOOP_CLIENT_SECRET
    }

    # Scambia code → token
    r = requests.post(TOKEN_URL, data=data, timeout=10)
    r.raise_for_status()
    tokens = r.json()    

    
    app.logger.warning(
        "WHOOP tokens received:\n"
        "  access_token = %s\n"
        "  refresh_token = %s\n"
        "  expires_in = %s",
        tokens["access_token"],
        tokens["refresh_token"],
        tokens["expires_in"]
    )

    # TODO: salva tokens in DB (user_id ➜ access_token, refresh_token, expires_at)

    return jsonify(ok=True), 200
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
