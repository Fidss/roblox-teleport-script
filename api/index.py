from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timezone

app = Flask(__name__, template_folder='../templates')

# URL dan API Key Supabase Anda
SUPABASE_URL = "https://kmyipabrhukygbashtwh.supabase.co/rest/v1/bots"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImtteWlwYWJyaHVreWdiYXNodHdoIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODI0ODMyMTIsImV4cCI6MjA5ODA1OTIxMn0.EQC95fFG2xeM0Wy5UiG55bo1ftx8sA7gS1etoTmOym0"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

@app.route('/')
def dashboard():
    return render_template('index.html')

# Endpoint 1: Tempat Roblox melakukan Polling berkala
@app.route('/api/poll', methods=['POST'])
def bot_poll():
    data = request.json or {}
    username = data.get('username')
    if not username:
        return jsonify({"error": "Username required"}), 400
    
    clean_username = username.strip().lower()
    current_time = datetime.now(timezone.utc).isoformat()

    # Cek apakah user sudah terdaftar di Supabase
    check_res = requests.get(f"{SUPABASE_URL}?username=eq.{clean_username}", headers=HEADERS)
    
    if check_res.status_code == 200 and len(check_res.json()) > 0:
        # Jika ada, update last_seen saja
        requests.patch(f"{SUPABASE_URL}?username=eq.{clean_username}", json={"last_seen": current_time}, headers=HEADERS)
    else:
        # Jika belum ada, daftarkan baru
        requests.post(SUPABASE_URL, json={"username": clean_username, "last_seen": current_time, "command": "none"}, headers=HEADERS)

    # Ambil status perintah (command) saat ini
    command = "none"
    get_cmd = requests.get(f"{SUPABASE_URL}?username=eq.{clean_username}&select=command", headers=HEADERS)
    if get_cmd.status_code == 200 and len(get_cmd.json()) > 0:
        command = get_cmd.json()[0].get('command', 'none')

    # Jika perintahnya respawn, langsung reset ke 'none' agar tidak mati berulang kali
    if command == "respawn":
        requests.patch(f"{SUPABASE_URL}?username=eq.{clean_username}", json={"command": "none"}, headers=HEADERS)

    return jsonify({"command": command})

# Endpoint 2: Mengambil semua data bot untuk Dashboard
@app.route('/api/users', methods=['GET'])
def get_users():
    res = requests.get(f"{SUPABASE_URL}?select=*&order=last_seen.desc", headers=HEADERS)
    if res.status_code == 200:
        return jsonify({"bots": res.json()})
    return jsonify({"bots": []})

# Endpoint 3: Mentargetkan perintah Respawn dari Dashboard ke Supabase
@app.route('/api/respawn', methods=['POST'])
def trigger_respawn():
    data = request.json or {}
    username = data.get('username')
    if not username:
        return jsonify({"error": "Username required"}), 400
    
    clean_username = username.strip().lower()
    res = requests.patch(f"{SUPABASE_URL}?username=eq.{clean_username}", json={"command": "respawn"}, headers=HEADERS)
    
    if res.status_code in [200, 201, 204]:
        return jsonify({"success": True})
    return jsonify({"error": "Gagal update database"}), 500
