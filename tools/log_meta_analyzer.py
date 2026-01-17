#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
log_meta_analyzer.py
- Parse radio_spot_watcher.log
- Extrait SPOT + événements SURGE
- Génère :
  - data/meta/spots_clean.csv
  - data/meta/summary.json
  - data/meta/bands_score.json
"""

import argparse
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


RE_SPOT = re.compile(
    r"""^(?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[INFO\]\s+TelnetWorker:\s+
        SPOT:\s+(?P<dx>[A-Z0-9/]+)\s+\((?P<band>[^,]+),\s+(?P<mode>[^)]+)\)\s+->\s+
        SPD:\s+(?P<spd>\d+)\s+pts\s+\(Dist:\s+(?P<dist>\d+)km\)
    """,
    re.VERBOSE,
)

RE_SURGE_START = re.compile(
    r"""^(?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[INFO\]\s+TelnetWorker:\s+
        ALERTE\s+SURGE\s+(?P<band>[^:]+):
    """,
    re.VERBOSE,
)

RE_SURGE_END = re.compile(
    r"""^(?P<ts>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})\s+\[INFO\]\s+TelnetWorker:\s+
        FIN\s+ALERTE\s+SURGE\s+(?P<band>[^:]+):
    """,
    re.VERBOSE,
)


def parse_ts(ts_str: str) -> datetime:
    # Log semble en horaire local du host. On garde "naive" mais cohérent.
    # Si tu veux forcer UTC : remplace par datetime.strptime(...).replace(tzinfo=timezone.utc)
    return datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")


def normalize_band(band: str) -> str:
    return band.strip().replace(" ", "")

def normalize_mode(mode: str) -> str:
    return mode.strip().upper().replace("-", "")


def compute_band_score(df: pd.DataFrame) -> pd.DataFrame:
    """
    Score simple, stable, utile :
    - pondère SPD et distance (log) pour éviter que les 10 000 km écrasent tout
    - ajoute un bonus si spot pendant surge
    """
    if df.empty:
        return pd.DataFrame(columns=["band", "score", "spots", "avg_spd", "avg_dist_km", "surge_ratio"])

    # poids distance (en milliers de km)
    dist_w = df["dist_km"].clip(lower=1) / 1000.0
    df = df.copy()
    df["score_item"] = df["spd"] * (1.0 + dist_w.apply(lambda x: math.log1p(x))) * (1.15 if "is_surge" in df.columns else 1.0)
    if "is_surge" in df.columns:
        df.loc[df["is_surge"] == True, "score_item"] *= 1.15

    g = df.groupby("band", as_index=False).agg(
        score=("score_item", "sum"),
        spots=("dx", "count"),
        avg_spd=("spd", "mean"),
        avg_dist_km=("dist_km", "mean"),
        surge_ratio=("is_surge", "mean") if "is_surge" in df.columns else ("dx", lambda s: 0.0),
    )
    # normalisation optionnelle (0-100)
    if len(g) > 0:
        mx = g["score"].max()
        if mx > 0:
            g["score_norm_0_100"] = (g["score"] / mx) * 100.0
        else:
            g["score_norm_0_100"] = 0.0
    return g.sort_values("score", ascending=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", default="radio_spot_watcher.log", help="Chemin du log")
    ap.add_argument("--outdir", default="data/meta", help="Dossier de sortie")
    ap.add_argument("--tail-lines", type=int, default=0, help="Si >0, n'analyse que les N dernières lignes (plus rapide)")
    args = ap.parse_args()

    log_path = Path(args.log)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    if not log_path.exists():
        raise SystemExit(f"Log introuvable: {log_path}")

    # Lecture
    with log_path.open("r", errors="ignore") as f:
        lines = f.readlines()

    if args.tail_lines and args.tail_lines > 0:
        lines = lines[-args.tail_lines :]

    surge_active = set()  # bandes en surge actuellement
    rows = []
    surge_events = []

    for line in lines:
        line = line.strip()

        m = RE_SURGE_START.match(line)
        if m:
            ts = parse_ts(m.group("ts"))
            band = normalize_band(m.group("band"))
            surge_active.add(band)
            surge_events.append({"ts": ts.isoformat(), "type": "SURGE_START", "band": band})
            continue

        m = RE_SURGE_END.match(line)
        if m:
            ts = parse_ts(m.group("ts"))
            band = normalize_band(m.group("band"))
            surge_active.discard(band)
            surge_events.append({"ts": ts.isoformat(), "type": "SURGE_END", "band": band})
            continue

        m = RE_SPOT.match(line)
        if m:
            ts = parse_ts(m.group("ts"))
            band = normalize_band(m.group("band"))
            mode = normalize_mode(m.group("mode"))
            dx = m.group("dx").strip()
            spd = int(m.group("spd"))
            dist_km = int(m.group("dist"))

            rows.append(
                {
                    "ts": ts,
                    "date": ts.date().isoformat(),
                    "hour": ts.hour,
                    "dx": dx,
                    "band": band,
                    "mode": mode,
                    "spd": spd,
                    "dist_km": dist_km,
                    "is_surge": band in surge_active,
                }
            )

    df = pd.DataFrame(rows)
    spots_csv = outdir / "spots_clean.csv"
    summary_json = outdir / "summary.json"
    bands_json = outdir / "bands_score.json"

    # Sortie vide propre
    if df.empty:
        df.to_csv(spots_csv, index=False)
        summary = {
            "generated_at": datetime.now().isoformat(),
            "log_path": str(log_path),
            "spots": 0,
            "range": None,
            "by_band": {},
            "by_mode": {},
            "top_spots": [],
            "surge_events": surge_events[-50:],
        }
        summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        bands_json.write_text(json.dumps([], ensure_ascii=False, indent=2), encoding="utf-8")
        return

    df = df.sort_values("ts")
    df.to_csv(spots_csv, index=False)

    # Stats basiques
    by_band = df["band"].value_counts().to_dict()
    by_mode = df["mode"].value_counts().to_dict()

    top_spots = (
        df.sort_values(["spd", "dist_km"], ascending=[False, False])
        .head(15)[["ts", "dx", "band", "mode", "spd", "dist_km", "is_surge"]]
        .assign(ts=lambda x: x["ts"].astype(str))
        .to_dict(orient="records")
    )

    # Heatmap (heure x bande) sous forme dictionnaire
    heat = (
        df.pivot_table(index="hour", columns="band", values="dx", aggfunc="count", fill_value=0)
        .sort_index()
    )
    heatmap = {
        "hours": [int(h) for h in heat.index.tolist()],
        "bands": [str(b) for b in heat.columns.tolist()],
        "matrix": heat.values.tolist(),
    }

    band_scores = compute_band_score(df)
    band_scores_records = band_scores.round(3).to_dict(orient="records")

    summary = {
        "generated_at": datetime.now().isoformat(),
        "log_path": str(log_path),
        "spots": int(len(df)),
        "range": {
            "start": str(df["ts"].iloc[0]),
            "end": str(df["ts"].iloc[-1]),
        },
        "by_band": by_band,
        "by_mode": by_mode,
        "dx": {
            "avg_spd": float(df["spd"].mean()),
            "max_spd": int(df["spd"].max()),
            "avg_dist_km": float(df["dist_km"].mean()),
            "max_dist_km": int(df["dist_km"].max()),
            "surge_ratio": float(df["is_surge"].mean()),
        },
        "top_spots": top_spots,
        "heatmap": heatmap,
        "surge_events_tail": surge_events[-200:],  # pour debug
    }

    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    bands_json.write_text(json.dumps(band_scores_records, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
