CREATE TABLE documenti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_produttore TEXT,
    destinazione TEXT,
    codice_eer TEXT,
    data_invio DATE,
    data_accettazione DATE,
    data_scadenza DATE
);

-- Tabella Produttori
CREATE TABLE produttori (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL
);

CREATE TABLE impianti (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_impianto TEXT NOT NULL,
    indirizzo_impianto TEXT NOT NULL
);
