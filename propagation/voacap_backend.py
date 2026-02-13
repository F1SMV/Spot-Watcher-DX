from datetime import datetime

DEFAULT_PATHS = [
    ("Regional", "LOCAL → LOCAL"),
    ("North America", "LOCAL → NA"),
    ("South America", "LOCAL → SA"),
    ("Africa", "LOCAL → AF"),
    ("Asia / Oceania", "LOCAL → AS/OC"),
]

def voacap_stub(label):
    return {
        "muf": 18 + (hash(label) % 10),
        "bands": ["20m", "17m"],
        "reliability": "good" if label == "Regional" else "moderate",
        "valid_hours": 3
    }

def generate_voacap_summary(qth):
    paths = []
    for label, path in DEFAULT_PATHS:
        data = voacap_stub(label)
        paths.append({
            "label": label,
            "path": path,
            **data
        })

    return {
        "qth": qth.get("locator"),
        "paths": paths,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source": "VOACAP model (stub)"
    }
