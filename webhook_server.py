import os, hmac, base64, hashlib
from flask import Flask, request, abort

app = Flask(__name__)

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
# ——— New health‐check endpoint ———
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify(status="ok"), 200
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
