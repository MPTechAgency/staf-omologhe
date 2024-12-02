import sqlite3

# Nome del database
DATABASE = 'database.db'

# Funzione per creare o aggiornare il database
def crea_o_aggiorna_db():
    # Connessione al database SQLite
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Creazione della tabella 'documenti' per la lista omologhe
    c.execute('''
        CREATE TABLE IF NOT EXISTS documenti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_produttore TEXT NOT NULL,
            impianto_destinazione TEXT NOT NULL,
            indirizzo_cantiere TEXT NOT NULL,
            codice_eer TEXT NOT NULL,
            data_invio DATE NOT NULL,
            data_accettazione DATE NOT NULL,
            data_scadenza DATE NOT NULL
        );
    ''')

    # Creazione della tabella 'produttori' per la lista produttori
    c.execute('''
        CREATE TABLE IF NOT EXISTS produttori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_produttore TEXT NOT NULL,
            indirizzo_produttore TEXT NOT NULL
        );
    ''')

    # Creazione della tabella 'impianti' per la lista impianti
    c.execute('''
        CREATE TABLE IF NOT EXISTS impianti (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_impianto TEXT NOT NULL,
            indirizzo_impianto TEXT NOT NULL
        );
    ''')

    # Creazione della tabella 'cassoni' per la gestione dei cassoni
    c.execute('''
        CREATE TABLE IF NOT EXISTS cassoni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_cliente TEXT NOT NULL,
            cantiere_destinazione TEXT NOT NULL,
            tipologia_cassone TEXT NOT NULL, -- Grande, Piccolo, 3/4
            altezza_cassone TEXT NOT NULL, -- Basso, Alto, Alto c/Cop
            data_consegna DATE NOT NULL,
            data_ritiro DATE, -- Opzionale
            nome_referente TEXT NOT NULL,
            numero_telefono TEXT NOT NULL,
            FOREIGN KEY (nome_cliente) REFERENCES produttori(nome_produttore)
        );
    ''')

    # Commit e chiusura della connessione
    conn.commit()
    conn.close()

    print("Database e tabelle creati o aggiornati con successo!")

# Esegui la funzione
crea_o_aggiorna_db()
