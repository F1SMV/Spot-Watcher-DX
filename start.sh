#!/bin/bash

# 1. Définition des couleurs pour les logs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[INIT] Démarrage de Radio Spot Watcher DX v6.1...${NC}"

# 2. Gestion du port 8000 (KILL PROCESS)
PORT=8000
PID=$(lsof -t -i:$PORT)

if [ -n "$PID" ]; then
    echo -e "${RED}[WARN] Le port $PORT est occupé par le PID $PID.${NC}"
    echo -e "${YELLOW}[ACTION] Arrêt forcé du processus $PID...${NC}"
    kill -9 $PID
    sleep 2
    echo -e "${GREEN}[OK] Port $PORT libéré.${NC}"
else
    echo -e "${GREEN}[OK] Le port $PORT est libre.${NC}"
fi

# 3. Vérification de l'environnement Python
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[INSTALL] Création de l'environnement virtuel...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${YELLOW}[INSTALL] Installation des dépendances...${NC}"
    pip install flask
else
    source venv/bin/activate
fi

# 4. Lancement de l'application
echo -e "${GREEN}[START] Lancement de l'application Flask...${NC}"
python3 webapp.py
