#!/bin/bash

echo "🛠️  Inizio installazione dei pacchetti necessari..."

# Controlla se l'utente ha i permessi di root
if [ "$(id -u)" != "0" ]; then
    echo "❌ Questo script deve essere eseguito come root. Usa 'sudo ./install.sh'."
    exit 1
fi

# Aggiornamento dei repository
echo "🔄 Aggiornamento dei repository..."
sudo apt-get update -y

# Installazione dei pacchetti necessari
echo "📦 Installazione di Python3 e strumenti correlati..."
sudo apt-get install -y python3 python3-pip python3-venv

# Creazione di un ambiente virtuale (opzionale ma consigliato)
if [ ! -d "venv" ]; then
    echo "🛠️  Creazione di un ambiente virtuale Python..."
    python3 -m venv venv
else
    echo "✅ Ambiente virtuale già esistente. Procedo..."
fi

# Attivazione dell'ambiente virtuale
source venv/bin/activate

# Installazione delle dipendenze Python
echo "📦 Installazione dei pacchetti Python necessari..."
pip install --upgrade pip
pip install flask flask_sqlalchemy flask_login flask_bcrypt apscheduler fuzzywuzzy python-dotenv

# Installazione delle dipendenze da requirements.txt (se presente)
if [ -f "requirements.txt" ]; then
    echo "📜 Trovato requirements.txt. Installazione delle dipendenze..."
    pip install -r requirements.txt
else
    echo "⚠️ Nessun requirements.txt trovato. Installazione manuale delle dipendenze completata."
fi

# Pulizia dei pacchetti inutilizzati
echo "🧹 Pulizia dei pacchetti inutilizzati..."
sudo apt-get autoremove -y

# Richiesta dell'indirizzo IP privato dell'utente
PRIVATE_IP=$(hostname -I | awk '{print $1}')
echo "🔍 Trovato IP privato: $PRIVATE_IP"

# Controllo del certificato HTTPS
if [ ! -f "cert.pem" ] || [ ! -f "key.pem" ]; then
    echo "🔒 Certificati HTTPS non trovati. Generazione di certificati autofirmati..."
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes -subj "/CN=localhost"
else
    echo "✅ Certificati HTTPS trovati."
fi

# Avvio dell'applicazione Flask
echo "🚀 Avvio dell'applicazione Flask su $PRIVATE_IP:5000..."
FLASK_APP=app.py flask run --host="$PRIVATE_IP" --port=5000 --cert=cert.pem --key=key.pem
