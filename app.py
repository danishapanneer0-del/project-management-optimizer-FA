"""
AI Resource & Schedule Optimizer — deployable web app.

Serves the app's page AND proxies AI requests to Claude from the same
server, using ONE Anthropic API key stored server-side as an environment
variable. Visitors never see or need their own key — the whole point of
deploying this is so a shared link works for anyone, including graders
who have no Anthropic account at all.

Local run:
    pip install -r requirements.txt
    export ANTHROPIC_API_KEY=sk-ant-...      (Windows: set ANTHROPIC_API_KEY=sk-ant-...)
    python app.py
    -> open http://localhost:5000

Deployment: see README-deploy.md in this folder for step-by-step
instructions (Render.com, free tier, ~10 minutes).
"""

import os
import urllib.request
import urllib.error

from flask import Flask, request, Response, jsonify, render_template

app = Flask(__name__)

ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "api_key_configured": bool(ANTHROPIC_API_KEY)})


@app.route("/v1/messages", methods=["POST"])
def proxy_messages():
    if not ANTHROPIC_API_KEY:
        return jsonify({
            "error": "ANTHROPIC_API_KEY is not set on the server. "
                     "Add it as an environment variable in your hosting dashboard "
                     "and redeploy."
        }), 500

    body = request.get_data()  # forward the app's JSON body to Anthropic, unmodified

    req = urllib.request.Request(
        ANTHROPIC_URL,
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": ANTHROPIC_VERSION,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return Response(resp.read(), status=resp.status, mimetype="application/json")
    except urllib.error.HTTPError as e:
        return Response(e.read(), status=e.code, mimetype="application/json")
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    if not ANTHROPIC_API_KEY:
        print("\n*** WARNING: ANTHROPIC_API_KEY is not set — AI features will fail until it is. ***\n")
    app.run(host="0.0.0.0", port=port)
