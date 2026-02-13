# propagation/voacap_hybrid.py

from datetime import datetime
from propagation.voacap_tables import VOACAP_TABLES

def weight_probability(p, band, sfi, kp, hour):
    # Solar Flux effect
    if band in ("15m","10m"):
        p *= 1 + max(0, (sfi - 100) / 100)

    # Geomagnetic penalty
    if kp >= 4:
        p *= 0.7
    if kp >= 6:
        p *= 0.5

    # Night boost for low bands
    if band in ("40m","30m") and (hour < 6 or hour > 20):
        p *= 1.2

    return max(0.0, min(p, 1.0))


def build_hourly_model(region, sfi, kp):
    base = VOACAP_TABLES.get(region, {})
    out = []

    for band, hours in base.items():
        band_hours = []
        for h, p in enumerate(hours):
            band_hours.append({
                "h": h,
                "p": round(weight_probability(p, band, sfi, kp, h), 2)
            })
        out.append({
            "band": band,
            "hours": band_hours
        })

    return out