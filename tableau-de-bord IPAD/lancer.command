#!/bin/bash
# Double-cliquer sur ce fichier (Mac) pour démarrer le tableau de bord.
cd "$(dirname "$0")"
[ -f .env ] || cp .env.exemple .env
IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null)
echo "Sur l'iPad, ouvrir Safari à l'adresse : http://${IP:-adresse-du-mac}:8765"
exec python3 serveur.py
