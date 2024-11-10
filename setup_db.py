import sqlite3

# Nome del database
DATABASE = 'database.db'

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
        indirizzo_produttore TEXT
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

# Commit e chiusura della connessione
conn.commit()
conn.close()

print("Database e tabelle creati con successo!")

