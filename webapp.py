import time
import telnetlib
import threading
import json
import os
import urllib.request
import feedparser
import ssl
import math 
from collections import deque
from flask import Flask, render_template, jsonify, request, abort, redirect, url_for 

# --- CONFIGURATION GENERALE ---
APP_VERSION = "NEURAL AI v3.5 - DX/MS READY"
MY_CALL = "F1SMV"
WEB_PORT = 8000
KEEP_ALIVE = 60
SPOT_LIFETIME = 1800 
SPD_THRESHOLD = 70
TOP_RANKING_LIMIT = 10 
DEFAULT_QRA = "JN23"

# --- CONFIGURATION SURGE ---
SURGE_WINDOW = 900
SURGE_THRESHOLD = 3.0
MIN_SPOTS_FOR_SURGE = 3

# --- CONFIGURATION ASTRO/MÉTEOR SCATTER ---
METEOR_SHOWERS = [
    {"name": "Quadrantides", "start": (1, 1), "end": (1, 7), "peak": (1, 3)},
    {"name": "Lyrides", "start": (4, 16), "end": (4, 25), "peak": (4, 22)},
    {"name": "Êta Aquarides", "start": (4, 20), "end": (5, 30), "peak": (5, 6)},
    {"name": "Perséides", "start": (7, 15), "end": (8, 24), "peak": (8, 12)},
    {"name": "Orionides", "start": (10, 1), "end": (11, 7), "peak": (10, 21)},
    {"name": "Léonides", "start": (11, 10), "end": (11, 23), "peak": (11, 17)},
    {"name": "Géminides", "start": (12, 4), "end": (12, 17), "peak": (12, 14)},
]
MSK144_FREQ = 144.360  
MSK144_TOLERANCE_KHZ = 10 / 1000

# --- DEFINITIONS BANDES ---
HF_BANDS = ['160m', '80m', '60m', '40m', '30m', '20m', '17m', '15m', '12m', '10m', '6m']
VHF_BANDS = ['4m', '2m', '70cm', '23cm', '13cm', 'QO-100']
HISTORY_BANDS = ['12m', '10m', '6m'] 

BAND_COLORS = {
    '160m': '#5c4b51', '80m': '#8e44ad', '60m': '#2c3e50',
    '40m': '#2980b9', '30m': '#16a085', '20m': '#27ae60',
    '17m': '#f1c40f', '15m': '#e67e22', '12m': '#d35400', 
    '10m': '#c0392b', 
    '6m': '#e84393', 
    '4m': '#ff9ff3', '2m': '#f1c40f', 
    '70cm': '#c0392b', '23cm': '#8e44ad', '13cm': '#bdc3c7',
    'QO-100': '#00a8ff' 
}

# --- DX CLUSTER CONFIGURATION (Fonctionnelle avec Failover) ---
RSS_URLS = ["https://www.dx-world.net/feed/"]
CLUSTERS = [
    ("dxfun.com", 8000),
    ("dx.f5len.org", 7300),
    ("gb7mbc.spud.club", 8000)
]
CTY_URL = "https://www.country-files.com/cty/cty.dat"
CTY_FILE = "cty.dat"
SOLAR_URL = "https://services.swpc.noaa.gov/text/wwv.txt"
WATCHLIST_FILE = "watchlist.json"

# --- CACHES GLOBAUX et INITIALISATION QTH ---
app = Flask(__name__)

spots_buffer = deque(maxlen=6000)
band_history = {}
prefix_db = {}
ticker_info = {"text": "SYSTEM INITIALIZATION..."}
watchlist = set()
surge_bands = [] 

history_24h = {band: [0] * 24 for band in HISTORY_BANDS}
history_lock = threading.Lock()
surge_lock = threading.Lock()


# --- PLAGES DE FREQUENCES CW MISES A JOUR ---
CW_RANGES = [
    ('160m', 1.810, 1.838), ('80m', 3.500, 3.560), ('40m', 7.000, 7.035),
    ('30m', 10.100, 10.134), ('20m', 14.000, 14.069), ('17m', 18.068, 18.095),
    ('15m', 21.000, 21.070), ('12m', 24.890, 24.913), ('10m', 28.000, 28.070),
]


# --- SSL BYPASS ---
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError: pass
else: ssl._create_default_https_context = _create_unverified_https_context


# --- FONCTIONS UTILITAIRES ET DE TRAITEMENT ---

def qra_to_lat_lon(qra):
    """ Convertit un QRA locator en latitude et longitude. """
    try:
        qra = qra.upper().strip()
        if len(qra) < 4: return None, None
        
        lon = -180 + (ord(qra[0]) - ord('A')) * 20
        lat = -90 + (ord(qra[1]) - ord('A')) * 10
        
        if len(qra) >= 4:
            lon += int(qra[2]) * 2
            lat += int(qra[3]) * 1
        
        if len(qra) >= 6:
            lon += (ord(qra[4]) - ord('A')) * (2/24) + (1/24)
            lat += (ord(qra[5]) - ord('A')) * (1/24) + (1/48)
        else:
            lon += 1
            lat += 0.5
            
        return lat, lon
    except:
        return None, None

# Initialisation du QTH utilisateur (doit être fait après la définition de qra_to_lat_lon)
user_qra = DEFAULT_QRA
initial_lat, initial_lon = qra_to_lat_lon(DEFAULT_QRA)
user_lat = initial_lat if initial_lat is not None else 43.10
user_lon = initial_lon if initial_lon is not None else 5.88


def is_meteor_shower_active():
    """ Vérifie si la date actuelle est dans une période d'essaim de météores (UTC). """
    now = time.gmtime(time.time())
    current_month = now.tm_mon
    current_day = now.tm_mday

    for shower in METEOR_SHOWERS:
        start_m, start_d = shower["start"]
        end_m, end_d = shower["end"]

        if start_m == end_m: 
            if current_month == start_m and start_d <= current_day <= end_d:
                return True, shower["name"]
        
        elif start_m < end_m: 
            if current_month == start_m and current_day >= start_d:
                return True, shower["name"]
            if current_month == end_m and current_day <= end_d:
                return True, shower["name"]
            if start_m < current_month < end_m:
                return True, shower["name"]
        
    return False, None


# --- Watchlist (fonctions inchangées) ---
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

# --- SURGE & HISTORY (avec mise à jour) ---
def record_surge_data(band):
    if band not in band_history: band_history[band] = deque()
    band_history[band].append(time.time())

def analyze_surges():
    """ Calcule les surges HF/VHF standard ET gère les surges MSK144. """
    
    # Correction: global doit être la première ligne si on modifie la variable globale
    global surge_bands 
    current_time = time.time()
    active_surges = []

    # --- 1. LOGIQUE MSK144 / METEOR SCATTER ---
    is_active, shower_name = is_meteor_shower_active()
    ms_surge_name = f"MSK144: {shower_name}" if is_active else "MSK144: Inactive"
    
    with surge_lock:
        # A. Détection MSK144
        recent_ms_spots = [
            s for s in spots_buffer 
            if s.get('band') == '2m' and s.get('mode') == 'MSK144' and (current_time - s['timestamp']) < 900
        ]
        
        if is_active and len(recent_ms_spots) >= 3:
            if ms_surge_name not in surge_bands:
                surge_bands.append(ms_surge_name)
                print(f"ALERTE MSK144: Surge MS détectée pendant les {shower_name}!")

        # B. Nettoyage MSK144 (Si l'essaim est terminé ou l'activité est retombée)
        if ms_surge_name in surge_bands and (not is_active or len(recent_ms_spots) < 2):
            surge_bands.remove(ms_surge_name)
            
        # --- 2. LOGIQUE HF/VHF STANDARD ---
        bands_to_remove = []
        for surge_name in surge_bands:
            if surge_name.startswith("MSK144:"): continue

            band = surge_name 
            
            timestamps = band_history.get(band, deque())
            while timestamps and timestamps[0] < current_time - SURGE_WINDOW:
                timestamps.popleft()
            
            count_total = len(timestamps)
            if count_total < 5: 
                bands_to_remove.append(band)
                continue 
                
            avg_rate = count_total / (SURGE_WINDOW / 60.0)
            recent_count = sum(1 for t in timestamps if t > current_time - 60)
            
            if recent_count > (avg_rate * SURGE_THRESHOLD) and recent_count >= MIN_SPOTS_FOR_SURGE:
                if band not in surge_bands:
                    surge_bands.append(band)
            else:
                bands_to_remove.append(band)

        active_surges = [s for s in surge_bands if s not in bands_to_remove]
        
        surge_bands = [s for s in surge_bands if s not in bands_to_remove]
        
        if ms_surge_name in surge_bands and ms_surge_name not in active_surges:
             active_surges.append(ms_surge_name)

    return active_surges


# --- MOTEUR DRSE (Score de Priorité de DX) ---
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371 
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c

def calculate_spd_score(call, band, mode, comment, country, lat, lon):
    global user_lat, user_lon
    
    score = 10 
    call = call.upper(); comment = (comment or "").upper()
    
    RARE_PREFIXES = [
        'DP0', 'DP1', 'RI1', '8J1', 'VP8', 'KC4', 
        '3Y', 'P5', 'BS7', 'CE0', 'CY9', 'EZ', 'FT5', 'FT8', 'VK0', 
        'HV', '1A', '4U1UN', 'E4', 'SV/A', 'T88', '9J', 'XU', '3D2', 'S21', 
        'KH0', 'KH1', 'KH3', 'KH4', 'KH7', 'KH9', 'KP1', 'KP5', 'ZK', 'ZL7', 'ZL9'
    ]
    
    is_rare = False
    for p in RARE_PREFIXES:
        if call.startswith(p): 
            score += 65 
            is_rare = True
            break 
    
    if 'UP' in comment or 'SPLIT' in comment: score += 15 
    if 'DX' in comment: score += 5
    if 'QRZ' in comment: score -= 10 
    if mode == 'CW': score += 10
    if 'PIRATE' in comment: score = 0
    
    if lat != 0.0 and lon != 0.0:
        dist_km = calculate_distance(user_lat, user_lon, lat, lon)
        if dist_km > 1000:
            distance_bonus = min(20, 20 * math.log10(dist_km / 1000))
            score += distance_bonus
    
    if band == 'QO-100': score += 40
    elif band in VHF_BANDS: score += 30 
    
    if band in ['10m', '12m', '15m']: score += 15 
    
    return min(int(score), 100)

def get_band_and_mode_smart(freq_float, comment):
    comment = (comment or "").upper()
    f = float(freq_float)
    
    if f < 1000: 
        f = f * 1000.0
    elif f > 20000000: 
        f = f / 1000.0

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
        if 10489000 <= freq_khz <= 10499000: return "QO-100"
        return "Unknown"

    band = find_band(f)
    f_mhz = f / 1000.0 
    mode = "SSB"
    
    for cw_band, min_mhz, max_mhz in CW_RANGES:
        if cw_band == band and min_mhz <= f_mhz <= max_mhz:
            mode = "CW"
            break
        
    if band == "2m" and abs(f_mhz - MSK144_FREQ) <= MSK144_TOLERANCE_KHZ:
        mode = "MSK144"
        return band, mode 
        
    if (3.557 <= f_mhz <= 3.587 or 7.069 <= f_mhz <= 7.079 or 10.130 <= f_mhz <= 10.140 or 
        14.071 <= f_mhz <= 14.077 or 18.097 <= f_mhz <= 18.103 or 21.071 <= f_mhz <= 21.077 or 
        24.913 <= f_mhz <= 24.919 or 28.069 <= f_mhz <= 28.079):   
        mode = "FT8"
        return band, mode 

    if mode != "CW":
        mode = "SSB" 
        if "FT8" in comment: mode = "FT8" 
        elif "FT4" in comment: mode = "FT4"
        elif "CW" in comment: mode = "CW"
        elif "FM" in comment: mode = "FM"
        elif "SSTV" in comment: mode = "SSTV"
        elif "PSK31" in comment: mode = "PSK31"
        elif "RTTY" in comment: mode = "RTTY"
        
    return band, mode

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
def history_maintenance_worker():
    global history_24h
    while True:
        now_utc = time.gmtime(time.time())
        sleep_seconds = (3600 - (now_utc.tm_min * 60 + now_utc.tm_sec)) + 5 
        time.sleep(sleep_seconds) 
        
        with history_lock:
            history_24h = {band: hist[1:] + [0] for band, hist in history_24h.items()}
            print(f"[{time.strftime('%H:%M:%S', time.gmtime())}] HISTORY 24H: Shifted and reset hour.")

def ticker_worker():
    while True:
        msgs = [f"SYSTEM ONLINE - {MY_CALL}"]
        try:
            req = urllib.request.Request(SOLAR_URL, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as r:
                l = [x for x in r.read().decode('utf-8').split('\n') if x and not x.startswith((':','#'))]
                if l: msgs.append(f"SOLAR: {l[-1]}")
        except: pass
        try:
            feed = feedparser.parse(RSS_URLS[0])
            if feed.entries:
                news = [entry.title for entry in feed.entries[:5]]
                msgs.append("NEWS: " + " | ".join(news))
        except Exception as e: 
            print(f"RSS Error: {e}")
        ticker_info["text"] = "   +++   ".join(msgs)
        time.sleep(1800) 

def telnet_worker():
    idx = 0
    while True:
        host, port = CLUSTERS[idx]
        print(f"[{time.strftime('%H:%M:%S')}] Tentative de connexion au Cluster: {host}:{port} ({idx + 1}/{len(CLUSTERS)})")
        try:
            tn = telnetlib.Telnet(host, port, timeout=15)
            try: tn.read_until(b"login: ", timeout=5)
            except: pass
            tn.write(MY_CALL.encode('ascii') + b"\n")
            time.sleep(1)
            tn.write(b"show/dx 50\n") 
            
            print(f"[{time.strftime('%H:%M:%S')}] Connexion établie sur {host}:{port}. Écoute des spots en cours.")
            last_ping = time.time()
            
            while True:
                try: line = tn.read_until(b"\n", timeout=2).decode('ascii', errors='ignore').strip()
                except: line = ""
                
                if not line:
                    if time.time() - last_ping > KEEP_ALIVE: 
                        tn.write(b"\n"); last_ping = time.time()
                    
                    analyze_surges() 
                    
                    continue
                
                if "DX de" in line:
                    try:
                        content = line[line.find("DX de")+5:].strip()
                        parts = content.split()
                        if len(parts) < 3: continue
                        freq_str = parts[1]
                        dx_call = parts[2].upper()
                        comment = " ".join(parts[3:]).upper()
                        
                        try: freq_raw = float(freq_str)
                        except: continue

                        band, mode = get_band_and_mode_smart(freq_raw, comment)
                        info = get_country_info(dx_call)
                        
                        spd_score = calculate_spd_score(dx_call, band, mode, comment, info['c'], info['lat'], info['lon'])
                        color = BAND_COLORS.get(band, '#00f3ff')
                        
                        record_surge_data(band)
                        
                        spot_obj = {
                            "timestamp": time.time(), "time": time.strftime("%H:%M"),
                            "freq": freq_str, "dx_call": dx_call, "band": band, "mode": mode,
                            "country": info['c'], "lat": info['lat'], "lon": info['lon'],
                            "score": spd_score, 
                            "is_wanted": spd_score >= SPD_THRESHOLD,
                            "via_eme": ("EME" in comment),
                            "color": color,
                            "type": "VHF" if band in VHF_BANDS else "HF"
                        }
                        spots_buffer.append(spot_obj)
                        print(f"SPOT: {dx_call} ({band}, {mode}) -> SPD: {spd_score} pts (Wanted: {spot_obj['is_wanted']})")
                    except Exception as e: 
                        pass 
                        
        except Exception as e: 
            print(f"[{time.strftime('%H:%M:%S')}] ERREUR CRITIQUE Cluster {host}:{port}: {e}. Basculement.")
            time.sleep(5)
            
        idx = (idx + 1) % len(CLUSTERS)


# --- ROUTES ---
@app.route('/')
def index():
    return render_template('index.html', version=APP_VERSION, my_call=MY_CALL, 
                           hf_bands=HF_BANDS, vhf_bands=VHF_BANDS, band_colors=BAND_COLORS,
                           spd_threshold=SPD_THRESHOLD, user_qra=user_qra) 

@app.route('/update_qra', methods=['POST'])
def update_qra():
    global user_qra, user_lat, user_lon
    
    new_qra = request.form.get('qra_locator', '').upper().strip()
    
    if not new_qra:
        return redirect(url_for('index'))
    
    new_lat, new_lon = qra_to_lat_lon(new_qra)
    
    valid = new_lat is not None and new_lon is not None
    
    if valid:
        user_qra = new_qra
        user_lat = new_lat
        user_lon = new_lon
        print(f"[{time.strftime('%H:%M:%S')}] QTH mis à jour: {user_qra} ({user_lat:.2f}, {user_lon:.2f})")
    
    return redirect(url_for('index')) 

@app.route('/user_location.json')
def get_user_location():
    global user_qra, user_lat, user_lon
    return jsonify({
        'qra': user_qra,
        'lat': user_lat,
        'lon': user_lon
    })

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

@app.route('/surge.json')
def get_surge_status():
    active_surges = analyze_surges()
    return jsonify({"surges": active_surges, "timestamp": time.time()})

@app.route('/wanted.json')
def get_ranking():
    now = time.time()
    active = [s for s in spots_buffer if (now - s['timestamp']) < SPOT_LIFETIME]
    
    def get_top_for_list(spot_list):
        ranked = sorted(spot_list, key=lambda x: x['score'], reverse=True)
        seen, top = set(), []
        for s in ranked:
            if s['dx_call'] not in seen:
                top.append(s)
                seen.add(s['dx_call'])
            if len(top) >= TOP_RANKING_LIMIT: break
        return top

    hf_spots = [s for s in active if s['type'] == 'HF']
    vhf_spots = [s for s in active if s['type'] == 'VHF']

    return jsonify({
        "hf": get_top_for_list(hf_spots),
        "vhf": get_top_for_list(vhf_spots)
    })

@app.route('/watchlist.json', methods=['GET', 'POST', 'DELETE'])
def manage_watchlist():
    if request.method == 'GET': return jsonify(sorted(list(watchlist)))
    data = request.get_json(force=True, silent=True)
    if not data or 'call' not in data: return abort(400)
    call = data['call'].upper().strip()
    if request.method == 'POST': watchlist.add(call)
    if request.method == 'DELETE' and call in watchlist: watchlist.remove(call)
    save_watchlist()
    return jsonify({"status": "ok"})

@app.route('/rss.json')
def get_rss(): return jsonify({"ticker": ticker_info["text"]})

@app.route('/history.json')
def get_history():
    now_hour = time.gmtime(time.time()).tm_hour
    
    labels = []
    for i in range(24):
        h = (now_hour - (23 - i)) % 24
        labels.append(f"H-{23-i} ({h:02}h)") 
        
    with history_lock:
        data = {band: list(hist) for band, hist in history_24h.items()} 

    current_data = {}
    for band in HISTORY_BANDS:
        hist_list = data[band]
        rotated = hist_list[(now_hour + 1) % 24:] + hist_list[:(now_hour + 1) % 24]
        current_data[band] = rotated
        
    return jsonify({"labels": labels, "data": current_data})


if __name__ == "__main__":
    load_cty_dat()
    load_watchlist()
    
    print(f"\n--- {APP_VERSION} ---")
    print(f"QTH de départ: {user_qra} ({user_lat:.2f}, {user_lon:.2f})")
    
    threading.Thread(target=telnet_worker, daemon=True).start()
    threading.Thread(target=ticker_worker, daemon=True).start()
    threading.Thread(target=history_maintenance_worker, daemon=True).start() 
    
    print(f"Server starting on http://0.0.0.0:{WEB_PORT}")
    app.run(host='0.0.0.0', port=WEB_PORT, debug=False, use_reloader=False)