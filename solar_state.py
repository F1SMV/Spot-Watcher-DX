# solar_state.py
import threading

solar_lock = threading.Lock()
solar_cache = {
    "sfi": "N/A",
    "a": "N/A",
    "k": "N/A",
    "kp": None,
    "kp_time_utc": None,
    "kp_a_running": None,
    "kp_station_count": None,
    "ts_utc": None
}
