#!/bin/bash

echo "🛠️  Inizio installazione dei pacchetti necessari..."

# Aggiornamento dei repository
sudo apt-get update

# Installazione dei pacchetti necessari
sudo apt-get install -y python3 python3-pip python3-venv

# Pulizia dei pacchetti inutilizzati
sudo apt-get autoremove -y

echo "🎉 Installazione completata con successo!"

# Creazione di un ambiente virtuale (opzionale ma consigliato)
if [ ! -d "venv" ]; then
    echo "🛠️  Creazione di un ambiente virtuale..."
    python3 -m venv venv
fi

# Attivazione dell'ambiente virtuale
source venv/bin/activate

# Installazione delle dipendenze specificate nel requirements.txt
echo "📦 Installazione delle dipendenze dal requirements.txt..."
pip install -r requirements.txt

# Richiesta dell'indirizzo IP privato dell'utente
PRIVATE_IP=$(hostname -I | awk '{print $1}')
echo "🔍 Trovato IP privato: $PRIVATE_IP"

# Modifica il file app.py per avviare l'app sul proprio IP
echo "🚀 Avvio dell'applicazione Flask su $PRIVATE_IP:5000..."

# Avvio dell'applicazione Flask con l'IP privato
FLASK_APP=app.py flask run --host="$PRIVATE_IP" --port=5000
