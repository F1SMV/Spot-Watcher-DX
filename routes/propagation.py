import os
from flask import Blueprint, jsonify
from propagation.voacap_hybrid import build_hourly_model
from solar_state import solar_cache, solar_lock

# Debug absolu : confirme quel fichier est chargé
print("### PROPAGATION LOADED FROM:", os.path.abspath(__file__))

propagation_bp = Blueprint("propagation", __name__)


@propagation_bp.route("/api/propagation/voacap/summary")
def voacap_summary():

    # ===============================
    # QTH FIXE (pour stabiliser)
    # ===============================
    lat = 43.5
    lon = 5.0

    # ===============================
    # Valeurs SAFE par défaut
    # (ne bloque JAMAIS)
    # ===============================
    sfi = 120.0      # SFI moyen
    kp = 2.0         # conditions calmes
    fallback = True  # on assume estimation au départ

    # ===============================
    # Lecture solaire thread-safe
    # ===============================
    with solar_lock:
        solar = dict(solar_cache)

    print("### VOACAP SUMMARY CALLED")
    print("DEBUG SOLAR RAW:", solar)

    # ===============================
    # Tentative d'utilisation
    # des vraies données solaires
    # ===============================
    try:
        raw_sfi = solar.get("sfi")
        raw_kp = solar.get("kp")

        if raw_sfi not in (None, "N/A"):
            sfi = float(raw_sfi)
            fallback = False

        if raw_kp is not None:
            kp = float(raw_kp)
            fallback = False

    except Exception as e:
        # On NE BLOQUE PAS
        print("DEBUG SOLAR PARSE ERROR:", e)

    print("DEBUG INPUTS:", lat, lon, sfi, kp, "fallback =", fallback)

    # ===============================
    # Calcul VOACAP hybride
    # ===============================
    try:
        model = build_hourly_model(lat, lon, sfi, kp)
    except Exception as e:
        print("DEBUG VOACAP ERROR:", e)
        model = None

    print("DEBUG MODEL:", model)

    # ===============================
    # AUCUN MODELE → réponse OK dégradée
    # ===============================
    if not model:
        return jsonify({
            "status": "ok",
            "note": "Propagation faible ou perturbée",
            "best_band": None,
            "snr": None,
            "reliability": None,
            "hour": None,
            "sfi": sfi,
            "kp": kp,
            "fallback": fallback
        })

    # ===============================
    # Modèle exploitable
    # ===============================
    best = max(model, key=lambda x: x.get("snr", 0))

    return jsonify({
        "status": "ok",
        "best_band": best.get("band"),
        "snr": round(best.get("snr", 0), 1),
        "reliability": round(best.get("reliability", 0) * 100),
        "hour": best.get("hour"),
        "sfi": sfi,
        "kp": kp,
        "fallback": fallback
    })
