#!/bin/bash
# ─────────────────────────────────────────────────────────
# pre-push-clean.sh — Nettoyage avant push GitHub
# Radio Spot Watcher DX — F1SMV
# Usage : ./pre-push-clean.sh && git push origin main
# ─────────────────────────────────────────────────────────

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd ~/Spot-Watcher-DX || { echo -e "${RED}Répertoire introuvable${NC}"; exit 1; }

echo -e "${YELLOW}[CLEAN] Nettoyage avant push...${NC}"

# 1. Fichiers à ne jamais pousser
SENSITIVE=(
    "watchlist.json"
    "watchlist.txt"
    "config.json"
    "config.local.py"
    "secrets.py"
    ".env"
)

for f in "${SENSITIVE[@]}"; do
    if git ls-files --error-unmatch "$f" &>/dev/null; then
        git rm --cached "$f"
        echo -e "${YELLOW}[CLEAN] Retiré du suivi : $f${NC}"
    fi
done

# 2. Logs
for f in $(git ls-files | grep -E '\.log(\.[0-9-]+)?$'); do
    git rm --cached "$f"
    echo -e "${YELLOW}[CLEAN] Log retiré : $f${NC}"
done

# 3. Dossier data/
if git ls-files data/ | grep -q .; then
    git rm -r --cached data/
    echo -e "${YELLOW}[CLEAN] Dossier data/ retiré du suivi${NC}"
fi

# 4. Fichiers temporaires Python
for f in $(git ls-files | grep -E '(__pycache__|\.pyc|\.pyo)'); do
    git rm --cached "$f"
    echo -e "${YELLOW}[CLEAN] Temporaire Python retiré : $f${NC}"
done

# 5. Vérification .gitignore présent
if [ ! -f .gitignore ]; then
    echo -e "${RED}[WARN] .gitignore manquant !${NC}"
fi

# 6. Résumé de ce qui va être poussé
echo ""
echo -e "${GREEN}[OK] Fichiers suivis par Git :${NC}"
git ls-files | grep -v "^templates/" | grep -v "^static/" | head -30

echo ""
echo -e "${GREEN}[READY] Prêt pour le push. Lance maintenant :${NC}"
echo -e "  git add -A && git commit -m 'votre message' && git push origin main"
