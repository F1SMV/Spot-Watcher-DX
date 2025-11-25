import time
import telnetlib
import threading
import json
import os
import urllib.request
import feedparser
from collections import deque
from flask import Flask, render_template, jsonify, request, abort

# --- CONFIGURATION ---
APP_VERSION = "NEURAL AI v1.3 " 
MY_CALL = "F1SMV"
WEB_PORT = 8000
KEEP_ALIVE = 60
SPOT_LIFETIME = 1800 
AI_SCORE_THRESHOLD = 50 
TOP_RANKING_LIMIT = 10 

# URL du flux RSS 
RSS_URL = "http://www.arrl.org/news/feed" 

CLUSTERS = [
    ("dxfun.com", 8000),
    ("dx.f5len.org", 7300),
    ("gb7mbc.spud.club", 8000)
]

CTY_URL = "https://www.country-files.com/cty/cty.dat"
CTY_FILE = "cty.dat"
SOLAR_URL = "https://services.swpc.noaa.gov/text/wwv.txt"
WATCHLIST_FILE = "watchlist.json"

# Listes complètes
ALL_BANDS = ['160m', '80m', '60m', '40m', '30m', '20m', '17m', '15m', '12m', '10m', '6m', '4m', '2m', '70cm', '23cm', '13cm', 'QO-100']
ALL_MODES = ['CW', 'SSB', 'AM', 'FM', 'FT8', 'FT4', 'RTTY', 'PSK', 'DATA']

RARE_PREFIXES = [
    '3Y', 'BS7', 'CE0', 'CY9', 'CY0', 'FT5', 'FT8', 'HK0', 'KH1', 'KH3', 
    'KH5', 'KH7K', 'KH9', 'KP1', 'KP5', 'P5', 'T3', 'VP8', 'VQ9', 'ZK', 
    'ZL9', 'ZS8', 'BV9', 'EZ', 'FR/G', 'VK0', 'TR8', 'DP0', 'TY', 'HV', 
    '1A', '4U', 'E4', 'SV/A', 'V47', 'T88', 'VP9'
]

app = Flask(__name__)
spots_buffer = deque(maxlen=5000)
prefix_db = {}
ticker_info = {"text": "Initialisation Neural Engine..."}
watchlist = set()

# --- Watchlist Persistence ---
def load_watchlist():
    global watchlist
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, "r") as f:
                data = json.load(f)
                watchlist = set([c.upper() for c in data if isinstance(c, str)])
        except: watchlist = set()

def save_watchlist():
    try:
        with open(WATCHLIST_FILE, "w") as f:
            json.dump(sorted(list(watchlist)), f, indent=2)
    except: pass

# --- IA CORE ---
def calculate_ai_score(call, band, mode, comment, country):
    score = 10 
    call = call.upper(); comment = (comment or "").upper()
    
    for p in RARE_PREFIXES:
        if call.startswith(p): score += 50; break 
    
    if 'UP' in comment or 'SPLIT' in comment: score += 15
    if 'DX' in comment: score += 5
    
    # Bonus VHF/UHF
    if band in ['6m', '4m', '2m', '70cm', '23cm', '13cm', 'QO-100']: score += 60
    if band in ['10m', '12m', '160m']: score += 20
    
    if mode == 'CW': score += 10
    if 'PIRATE' in comment: score = 0
    
    return min(score, 100)

# --- LOGIQUE BANDES & MODES (CORRIGÉE) ---
def get_band_and_mode_smart(freq_float, comment):
    comment = (comment or "").upper()
    f = float(freq_float)
    
    # Normalisation kHz
    if f < 1000: f = f * 1000.0
    if f > 1000000: f = f / 1000.0

    # 1. Détection FT8/FT4 par fréquence exacte (+/- tolérance)
    ft8_centers = [1840, 3573, 5357, 7074, 10136, 14074, 18100, 21074, 24915, 28074, 50313, 144174]
    ft4_centers = [3575, 7047, 10140, 14080, 18104, 21140, 24919, 28180, 50318]
    tol = 2.0 # Tolérance élargie à 2kHz

    def find_band(freq_khz):
        if 1800 <= freq_khz <= 2000: return "160m"
        if 3500 <= freq_khz <= 3800: return "80m"
        if 5300 <= freq_khz <= 5450: return "60m"
        if 7000 <= freq_khz <= 7300: return "40m"
        if 10100 <= freq_khz <= 10150: return "30m"
        if 14000 <= freq_khz <= 14350: return "20m"
        if 18068 <= freq_khz <= 18168: return "17m"
        if 21000 <= freq_khz <= 21450: return "15m"
        if 24890 <= freq_khz <= 24990: return "12m"
        if 28000 <= freq_khz <= 29700: return "10m"
        if 50000 <= freq_khz <= 54000: return "6m"
        if 70000 <= freq_khz <= 70500: return "4m"
        if 144000 <= freq_khz <= 146000: return "2m"
        if 430000 <= freq_khz <= 440000: return "70cm"
        if 1240000 <= freq_khz <= 1300000: return "23cm"
        if freq_khz > 10000000: return "QO-100"
        return "Unknown"

    band = find_band(f)

    # Vérification prioritaire Fréquences Digi
    for c in ft8_centers:
        if abs(f - c) <= tol: return band, "FT8"
    for c in ft4_centers:
        if abs(f - c) <= tol: return band, "FT4"

    # 2. Analyse du Commentaire (Priorité absolue si explicite)
    if "FT8" in comment: return band, "FT8"
    if "FT4" in comment: return band, "FT4"
    if "CW" in comment: return band, "CW"
    if "RTTY" in comment: return band, "RTTY"
    if "PSK" in comment: return band, "PSK"
    if "SSB" in comment or "USB" in comment or "LSB" in comment: return band, "SSB"
    if "FM" in comment: return band, "FM"

    # 3. Band Plan Logic (Le correctif est ici)
    # Si le mode est inconnu, on devine selon la portion de bande
    mode = "DATA" # Valeur par défaut temporaire

    if band == "160m":
        mode = "CW" if f < 1840 else "SSB"
    elif band == "80m":
        mode = "CW" if f < 3600 else "SSB"
    elif band == "40m":
        mode = "CW" if f < 7050 else "SSB"
    elif band == "30m":
        mode = "CW" if f < 10130 else "DATA" # 30m est data/cw only
    elif band == "20m":
        mode = "CW" if f < 14100 else "SSB"
    elif band == "17m":
        mode = "CW" if f < 18110 else "SSB"
    elif band == "15m":
        mode = "CW" if f < 21150 else "SSB"
    elif band == "12m":
        mode = "CW" if f < 24930 else "SSB"
    elif band == "10m":
        mode = "CW" if f < 28300 else "SSB"
    elif band in ["6m", "2m", "70cm"]:
        # En VHF DX, le bas de bande est souvent CW/SSB, le haut FM
        if "FM" in comment: 
            mode = "FM"
        elif band == "2m" and f > 144400:
            mode = "FM"
        else:
            mode = "SSB" # Par défaut en DX VHF on assume SSB si pas précisé

    return band, mode

# --- CTY ---
def load_cty_dat():
    global prefix_db
    if not os.path.exists(CTY_FILE):
        try: urllib.request.urlretrieve(CTY_URL, CTY_FILE)
        except: return
    try:
        with open(CTY_FILE, "rb") as f: raw = f.read().decode('latin-1')
        for rec in raw.replace('\r', '').replace('\n', ' ').split(';'):
            if ':' in rec:
                p = rec.split(':')
                country = p[0].strip()
                try: lat, lon = float(p[4]), float(p[5]) * -1
                except: lat, lon = 0.0, 0.0
                prefixes = p[7].strip().split(',')
                if len(p)>8: prefixes += p[8].strip().split(',')
                for px in prefixes:
                    clean = px.split('(')[0].split('[')[0].strip().lstrip('=')
                    if clean: prefix_db[clean] = {'c': country, 'lat': lat, 'lon': lon}
    except: pass

def get_country_info(call):
    call = call.upper()
    best = {'c': 'Unknown', 'lat': 0.0, 'lon': 0.0}
    longest = 0
    candidates = [call]
    if '/' in call: candidates.append(call.split('/')[-1])
    for c in candidates:
        for i in range(len(c), 0, -1):
            sub = c[:i]
            if sub in prefix_db and len(sub) > longest:
                longest = len(sub); best = prefix_db[sub]
    return best

# --- WORKERS ---
def ticker_worker():
    while True:
        msgs = [f"SYSTEM ONLINE - {MY_CALL}"]
        
        # 1. Solar Data (NOAA)
        try:
            with urllib.request.urlopen(SOLAR_URL, timeout=10) as r:
                l = [x for x in r.read().decode('utf-8').split('\n') if x and not x.startswith((':','#'))]
                if l: msgs.append(f"SOLAR: {l[-1]}")
        except: pass
        
        # 2. RSS News (Feedparser)
        try:
            feed = feedparser.parse(RSS_URL)
            if feed.entries:
                headlines = []
                for entry in feed.entries[:3]: # Prend les 3 premiers
                    headlines.append(entry.title.upper())
                if headlines:
                    msgs.append("NEWS: " + " +++ ".join(headlines))
            else:
                print("RSS: Pas d'entrées trouvées.")
        except Exception as e:
            print(f"RSS Error: {e}")

        ticker_info["text"] = "   +++   ".join(msgs)
        time.sleep(900) # Mise à jour toutes les 15 min

def telnet_worker():
    idx = 0
    while True:
        host, port = CLUSTERS[idx]
        print(f"Connexion au cluster: {host}:{port}")
        try:
            tn = telnetlib.Telnet(host, port, timeout=15)
            try: tn.read_until(b"login: ", timeout=5)
            except: pass
            tn.write(MY_CALL.encode('ascii') + b"\n")
            time.sleep(1)
            # On demande les derniers spots au démarrage pour remplir le tableau
            tn.write(b"show/dx 20\n")
            
            last_ping = time.time()
            while True:
                try:
                    line = tn.read_until(b"\n", timeout=2).decode('ascii', errors='ignore').strip()
                except:
                    line = ""

                if not line:
                    if time.time() - last_ping > KEEP_ALIVE: 
                        tn.write(b"\n")
                        last_ping = time.time()
                    continue
                
                if "DX de" in line:
                    try:
                        # Format typique: "DX de SPOTTER: FREQ CALL COMMENT TIME"
                        # On cherche "DX de" et on coupe après
                        content = line[line.find("DX de")+5:].strip()
                        # content ressemble à "F1SMV: 14000.0 W1AW CW 1200Z" ou "F1SMV 14000.0..."
                        
                        parts = content.split()
                        # parts[0] = Spotter (ex: "K1ABC:")
                        # parts[1] = Freq (ex: "14020.0")
                        # parts[2] = DX Call (ex: "TM100")
                        # parts[3...] = Comment
                        
                        if len(parts) < 3: continue
                        
                        freq_str = parts[1]
                        dx_call = parts[2].upper()
                        
                        # Reconstitution du commentaire
                        comment = " ".join(parts[3:]).upper()
                        
                        # Nettoyage fréquence (parfois collée à :)
                        if ":" in parts[0] and len(parts[0]) > 8: 
                            # Cas rare de collage malformé
                            continue

                        try:
                            freq_raw = float(freq_str)
                        except ValueError:
                            continue

                        via_eme = False
                        if "EME" in comment or "MOON" in comment: via_eme = True

                        band, mode = get_band_and_mode_smart(freq_raw, comment)
                        info = get_country_info(dx_call)
                        score = calculate_ai_score(dx_call, band, mode, comment, info['c'])
                        
                        spot_obj = {
                            "timestamp": time.time(), 
                            "time": time.strftime("%H:%M"),
                            "freq": freq_str, 
                            "dx_call": dx_call, 
                            "band": band, 
                            "mode": mode,
                            "country": info['c'], 
                            "lat": info['lat'], 
                            "lon": info['lon'],
                            "score": score, 
                            "is_wanted": score >= AI_SCORE_THRESHOLD,
                            "via_eme": via_eme
                        }
                        spots_buffer.append(spot_obj)
                        print(f"SCAN: {dx_call} [{band}/{mode}] -> {score}")
                    except Exception as e: 
                        print(f"Error parsing line: {line} -> {e}")
        except Exception as e:
            print(f"Cluster error ({host}): {e}")
        
        time.sleep(5)
        idx = (idx + 1) % len(CLUSTERS)

# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html', version=APP_VERSION, my_call=MY_CALL, date=time.strftime("%d/%m/%Y"), bands=ALL_BANDS, modes=ALL_MODES)

@app.route('/spots.json')
def get_spots():
    now = time.time()
    filter_band = request.args.get('band')
    filter_mode = request.args.get('mode')
    all_spots = [s for s in spots_buffer if (now - s['timestamp']) < SPOT_LIFETIME]
    if filter_band and filter_band != "All":
        all_spots = [s for s in all_spots if s['band'] == filter_band]
    if filter_mode and filter_mode != "All":
        all_spots = [s for s in all_spots if s['mode'] == filter_mode]
    return jsonify(list(reversed(all_spots)))

@app.route('/wanted.json')
def get_ranking():
    now = time.time()
    active = [s for s in spots_buffer if (now - s['timestamp']) < SPOT_LIFETIME]
    wanted = []
    for s in active:
        if not s.get('is_wanted'): continue
        if s.get('band') == '70cm' and not s.get('via_eme'): continue
        wanted.append(s)
        
    ranked = sorted(wanted, key=lambda x: x['score'], reverse=True)
    seen, top = set(), []
    for s in ranked:
        if s['dx_call'] not in seen:
            top.append({
                'call': s['dx_call'], 
                'score': s['score'], 
                'c': s['country'], 
                'band': s['band'],
                'freq': s['freq']
            })
            seen.add(s['dx_call'])
        if len(top) >= TOP_RANKING_LIMIT: break
    return jsonify(top)

@app.route('/watchlist.json', methods=['GET', 'POST', 'DELETE'])
def manage_watchlist():
    if request.method == 'GET':
        return jsonify(sorted(list(watchlist)))
    
    data = request.get_json(force=True, silent=True)
    if not data or 'call' not in data: return abort(400)
    call = data['call'].upper().strip()
    
    if request.method == 'POST':
        if call: watchlist.add(call)
        save_watchlist()
        return jsonify({"status": "added"})
    
    if request.method == 'DELETE':
        if call in watchlist: watchlist.remove(call)
        save_watchlist()
        return jsonify({"status": "removed"})

@app.route('/rss.json')
def get_rss(): return jsonify({"ticker": ticker_info["text"]})

if __name__ == "__main__":
    if not os.path.exists('templates'): os.makedirs('templates')
    load_cty_dat()
    load_watchlist()
    threading.Thread(target=telnet_worker, daemon=True).start()
    threading.Thread(target=ticker_worker, daemon=True).start()
    app.run(host='0.0.0.0', port=WEB_PORT, debug=False)
