#!/bin/bash

# Script di installazione per un'applicazione Flask

echo "🛠️  Inizio dell'installazione..."

# Funzione per installare un pacchetto se non è già installato
install_if_missing() {
    PACKAGE=$1
    if ! dpkg -s "$PACKAGE" &> /dev/null; then
        echo "📦 Installazione di $PACKAGE..."
        sudo apt update
        sudo apt install -y "$PACKAGE"
    else
        echo "✅ $PACKAGE è già installato."
    fi
}

# Verifica se Python è installato
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 non è installato. Installalo prima di procedere."
    exit 1
else
    echo "✅ Python3 è già installato."
fi

# Verifica se pip è installato
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 non è installato. Installazione in corso..."
    sudo apt update
    sudo apt install -y python3-pip
else
    echo "✅ pip3 è già installato."
fi

# Verifica se il modulo venv è installato
if ! python3 -m venv --help &> /dev/null; then
    echo "❌ python3-venv non è installato. Installazione in corso..."
    sudo apt update
    sudo apt install -y python3-venv
else
    echo "✅ python3-venv è già installato."
fi

# Crea un ambiente virtuale
if [ ! -d "venv" ]; then
    echo "🐍 Creazione dell'ambiente virtuale..."
    python3 -m venv venv
else
    echo "✅ L'ambiente virtuale esiste già."
fi

# Attiva l'ambiente virtuale
echo "✅ Attivazione dell'ambiente virtuale..."
source venv/bin/activate

# Aggiorna pip
echo "⬆️  Aggiornamento di pip..."
pip install --upgrade pip

# Installa i pacchetti dai requirements.txt
if [ -f "requirements.txt" ]; then
    echo "📦 Installazione dei pacchetti da requirements.txt..."
    pip install -r requirements.txt
else
    echo "❌ Il file requirements
