# Staf Omologhe

## Utilizzo

- Installa le dipendenze con lo script 'install.sh'

    ```bash
    ./install.sh
    ```

- Inizializza il database

    ```bash
    python3 setup_db.py
    ```

- Genera la chiave di sicurezza per il database (la password va scelta a piacere, le altre informazioni non sono necessarie)

    ```bash
    openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365
    ```

## TODO

- stile css dark mode
- La data di Accettazione può non essere immessa subito
