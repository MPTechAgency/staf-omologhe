-- Crea il database e le tabelle necessarie

-- Creazione della tabella 'documenti' per la lista omologhe
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

-- Creazione della tabella 'produttori' per la lista produttori
CREATE TABLE IF NOT EXISTS produttori (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_produttore TEXT NOT NULL,
    indirizzo_produttore TEXT
);

-- Creazione della tabella 'impianti' per la lista impianti
CREATE TABLE IF NOT EXISTS impianti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_impianto TEXT NOT NULL,
    indirizzo_impianto TEXT NOT NULL
);
