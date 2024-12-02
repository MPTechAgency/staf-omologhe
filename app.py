from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from apscheduler.schedulers.background import BackgroundScheduler
from dateutil.relativedelta import relativedelta
from fuzzywuzzy import process
import ssl

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE = 'database.db'

# Funzione per connettersi al database SQLite
def get_db_connection():
    # Usa 'check_same_thread=False' e il timeout per gestire meglio la concorrenza
    conn = sqlite3.connect(DATABASE, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    # Opzionale: Abilita il WAL per migliorare le performance con molte scritture
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn

# Funzione per gestire la conversione della data
def convert_date(date_string):
    if isinstance(date_string, str):
        try:
            # Prova a fare il parsing con il formato completo (data e ora)
            return datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            try:
                # Se fallisce, prova a fare il parsing solo con la data
                return datetime.strptime(date_string, '%Y-%m-%d')
            except ValueError:
                print(f"Formato data non riconosciuto: {date_string}")
                return None
    return date_string

# Funzione per verificare se il documento è scaduto
def isExpired(data_scadenza):
    # Se data_scadenza è già un oggetto datetime, non chiamare strptime
    if isinstance(data_scadenza, datetime):
        return data_scadenza < datetime.now()
    # Se data_scadenza è una stringa, convertila prima in datetime
    elif isinstance(data_scadenza, str):
        data_scadenza = convert_date(data_scadenza)
        if data_scadenza:
            return data_scadenza < datetime.now()
        else:
            return False
    return False  # Ritorna False se data_scadenza non è né str né datetime

app.jinja_env.globals.update(isExpired=isExpired)

# Calcolo automatico della data di scadenza (1 anno dopo la data di accettazione)
def calcola_data_scadenza(data_accettazione):
    data_accettazione_dt = convert_date(data_accettazione)
    scadenza = data_accettazione_dt + relativedelta(years=1)
    return scadenza.strftime('%Y-%m-%d')  # Restituisce la data nel formato 'YYYY-MM-DD'

# Funzione per inviare l'email di notifica
def send_email(subject, body):
    try:
        sender_email = "test@test.it"  # Cambia con l'email del mittente
        receiver_email = "test-invio@test.it"  # Cambia con l'email del destinatario
        password = "Password-test"  # Cambia con la password dell'email

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP_SSL('mx.test.it', 465)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()

        print(f"Email inviata a {receiver_email}")
    except Exception as e:
        print(f"Errore durante l'invio dell'email: {e}")

def check_expiring_documents():
    conn = get_db_connection()
    oggi = datetime.now()
    trenta_giorni = oggi + timedelta(days=30)
    cinque_giorni = oggi + timedelta(days=5)

    # Verifica documenti in scadenza tra oggi e 30 giorni
    documenti_30 = conn.execute('''
        SELECT * FROM documenti WHERE data_scadenza BETWEEN ? AND ?
    ''', (oggi.strftime('%Y-%m-%d'), trenta_giorni.strftime('%Y-%m-%d'))).fetchall()

    # Verifica documenti in scadenza tra 5 e 30 giorni
    documenti_5 = conn.execute('''
        SELECT * FROM documenti WHERE data_scadenza BETWEEN ? AND ?
    ''', (cinque_giorni.strftime('%Y-%m-%d'), trenta_giorni.strftime('%Y-%m-%d'))).fetchall()

    # Invia email per documenti che scadono in 30 giorni
    for doc in documenti_30:
        subject = f"Alert: Il documento di {doc['nome_produttore']} sta per scadere tra 30 giorni"
        body = f"Il documento di {doc['nome_produttore']} sta per scadere il {doc['data_scadenza']}."
        send_email(subject, body)

    # Invia email per documenti che scadono in 5 giorni
    for doc in documenti_5:
        subject = f"Alert: Il documento di {doc['nome_produttore']} sta per scadere tra 5 giorni"
        body = f"Il documento di {doc['nome_produttore']} sta per scadere il {doc['data_scadenza']} tra 5 giorni."
        send_email(subject, body)

    conn.close()

# Pianifica la funzione per eseguire ogni giorno
scheduler = BackgroundScheduler()
scheduler.add_job(check_expiring_documents, 'interval', days=1)
scheduler.start()

print("Scheduler avviato. L'alert verrà inviato ogni giorno.")

# Homepage
@app.route('/')
def home():
    return render_template('index.html')

# Lista Omologhe: Visualizza tutti i documenti
@app.route('/omologhe', methods=['GET'])
def lista_omologhe():
    try:
        query = request.args.get('query', '')  # Ottieni la query di ricerca dalla richiesta, se presente
        conn = get_db_connection()

        # Esegui la query SQL con la ricerca
        if query:
            # Usa LIKE per cercare in nome_produttore, indirizzo_cantiere, codice_eer, impianto_destinazione
            documenti = conn.execute('''SELECT * FROM documenti WHERE
                nome_produttore LIKE ? OR impianto_destinazione LIKE ? OR indirizzo_cantiere LIKE ? OR codice_eer LIKE ?''',
                ('%' + query + '%',) * 4).fetchall()
        else:
            # Se non c'è query, prendi tutti i documenti
            documenti = conn.execute('SELECT * FROM documenti').fetchall()

        conn.close()

        # Crea una nuova lista di dizionari mutabili
        documenti_formattati = []

        # Converte le date in oggetti datetime, se necessario
        for documento in documenti:
            documento_dict = dict(documento)  # Converte in dizionario mutabile

            # Converte i campi data_invio, data_accettazione, data_scadenza
            documento_dict['data_invio'] = convert_date(documento_dict.get('data_invio'))
            documento_dict['data_accettazione'] = convert_date(documento_dict.get('data_accettazione'))
            documento_dict['data_scadenza'] = convert_date(documento_dict.get('data_scadenza'))

            # Verifica che le date non siano None
            if None in (documento_dict['data_invio'], documento_dict['data_accettazione'], documento_dict['data_scadenza']):
                print(f"Date non valide per il documento ID {documento_dict.get('id')}")
                continue  # Salta questo documento

            # Aggiungi il documento formattato alla lista
            documenti_formattati.append(documento_dict)

        return render_template('lista_omologhe.html', documenti=documenti_formattati, query=query, isExpired=isExpired)
    except Exception as e:
        print(f"Errore in lista_omologhe: {e}")
        return str(e), 500

# Aggiungi Omologa: Modifica o aggiungi un nuovo documento
@app.route('/aggiungi_omologa', methods=['GET', 'POST'])
def aggiungi_omologa():
    conn = get_db_connection()

    # Recupera la lista dei produttori
    produttori = conn.execute('SELECT * FROM produttori').fetchall()

    # Recupera la lista degli impianti
    impianti = conn.execute('SELECT * FROM impianti').fetchall()

    conn.close()

    if request.method == 'POST':
        # Recupera i dati dal form
        document_id = request.form.get('id')  # id del documento, se presente per aggiornare
        nome_produttore = request.form.get('nome_produttore')
        impianto_destinazione = request.form.get('impianto_destinazione')
        codice_eer = request.form.get('codice_eer')
        data_invio = request.form.get('data_invio')
        data_accettazione = request.form.get('data_accettazione')
        indirizzo_cantiere = request.form.get('indirizzo_cantiere')  # Recupera l'indirizzo del cantiere

        # Calcola la data di scadenza in base alla data di accettazione
        data_scadenza = calcola_data_scadenza(data_accettazione)

        # Riapri la connessione per l'operazione di aggiornamento o inserimento
        conn = get_db_connection()

        # Se document_id è presente, aggiorniamo il documento esistente
        if document_id:
            conn.execute('''UPDATE documenti 
                            SET nome_produttore = ?, 
                                impianto_destinazione = ?, 
                                codice_eer = ?, 
                                data_invio = ?, 
                                data_accettazione = ?, 
                                data_scadenza = ?, 
                                indirizzo_cantiere = ?
                            WHERE id = ?''', 
                            (nome_produttore, impianto_destinazione, codice_eer, data_invio, data_accettazione, data_scadenza, indirizzo_cantiere, document_id))
        else:
            # Se document_id non è presente, inseriamo un nuovo documento
            conn.execute('''INSERT INTO documenti (nome_produttore, impianto_destinazione, codice_eer, data_invio, data_accettazione, data_scadenza, indirizzo_cantiere) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                            (nome_produttore, impianto_destinazione, codice_eer, data_invio, data_accettazione, data_scadenza, indirizzo_cantiere))

        conn.commit()  # Salviamo le modifiche nel database
        conn.close()   # Chiudiamo la connessione al database

        flash('Omologa aggiunta con successo!', 'success')  # Messaggio di successo
        return redirect(url_for('lista_omologhe'))  # Reindirizza alla lista delle omologhe

    # Se la richiesta è di tipo GET, renderizza il modulo di aggiunta
    return render_template('aggiungi_omologa.html', produttori=produttori, impianti=impianti)

# Modifica un documento esistente
@app.route('/modifica_omologa/<int:documento_id>', methods=['GET', 'POST'])
def modifica_omologa(documento_id):
    conn = get_db_connection()

    # Recupera il documento dal database
    documento = conn.execute('SELECT * FROM documenti WHERE id = ?', (documento_id,)).fetchone()
    if documento is None:
        return 'Documento non trovato', 404

    # Recupera la lista dei produttori e degli impianti dal database
    produttori = conn.execute('SELECT * FROM produttori').fetchall()
    impianti = conn.execute('SELECT * FROM impianti').fetchall()

    conn.close()

    # Convertire il risultato in un dizionario per modificarlo
    documento = dict(documento)

    # Utilizza la funzione convert_date per gestire le date
    documento['data_invio'] = convert_date(documento.get('data_invio'))
    documento['data_accettazione'] = convert_date(documento.get('data_accettazione'))
    documento['data_scadenza'] = convert_date(documento.get('data_scadenza'))

    if request.method == 'POST':
        # Ricevi i dati modificati dal form
        nome_produttore = request.form['nome_produttore']
        impianto_destinazione = request.form['impianto_destinazione']
        indirizzo_cantiere = request.form['indirizzo_cantiere']
        codice_eer = request.form['codice_eer']
        data_invio = request.form['data_invio']
        data_accettazione = request.form['data_accettazione']

        # Converte le date da stringa a datetime utilizzando convert_date
        data_invio = convert_date(data_invio)
        data_accettazione = convert_date(data_accettazione)

        # Calcolare la data di scadenza automaticamente (1 anno dopo la data di accettazione)
        data_scadenza = data_accettazione + relativedelta(years=1)

        # Esegui l'aggiornamento nel database
        conn = get_db_connection()
        conn.execute(''' 
            UPDATE documenti
            SET nome_produttore = ?, impianto_destinazione = ?, indirizzo_cantiere = ?, codice_eer = ?, 
                data_invio = ?, data_accettazione = ?, data_scadenza = ?
            WHERE id = ?
        ''', (
            nome_produttore, impianto_destinazione, indirizzo_cantiere, codice_eer,
            data_invio.strftime('%Y-%m-%d %H:%M:%S'),
            data_accettazione.strftime('%Y-%m-%d %H:%M:%S'),
            data_scadenza.strftime('%Y-%m-%d %H:%M:%S'),
            documento_id
        ))
        conn.commit()
        conn.close()

        # Reindirizza alla lista delle omologhe dopo la modifica
        return redirect(url_for('lista_omologhe'))

    # Passa i dati al template
    return render_template('modifica_omologa.html', documento=documento, produttori=produttori, impianti=impianti)


# Lista Produttori: Visualizza tutti i produttori
@app.route('/lista_produttori', methods=['GET'])
def lista_produttori():
    # Ottieni il parametro di ricerca 'query' dalla richiesta GET (se esiste)
    query = request.args.get('query', '')

    conn = get_db_connection()

    # Se c'è una query, filtra i produttori per nome
    if query:
        produttori = conn.execute('''
            SELECT * FROM produttori
            WHERE nome_produttore LIKE ?
        ''', ('%' + query + '%',)).fetchall()
    else:
        # Se non c'è query, restituisci tutti i produttori
        produttori = conn.execute('SELECT * FROM produttori').fetchall()

    conn.close()

    # Passa i dati alla template per la visualizzazione
    return render_template('lista_produttori.html', produttori=produttori, query=query)

# Aggiungi Produttore
@app.route('/aggiungi_produttore', methods=['GET', 'POST'])
def aggiungi_produttore():
    if request.method == 'POST':
        nome_produttore = request.form['nome_produttore']
        indirizzo_produttore = request.form['indirizzo_produttore']

        with get_db_connection() as conn:
            conn.execute('INSERT INTO produttori (nome_produttore, indirizzo_produttore) VALUES (?, ?)', (nome_produttore, indirizzo_produttore))
            conn.commit()

        flash('Produttore aggiunto con successo!', 'success')
        return redirect(url_for('lista_produttori'))

    return render_template('aggiungi_produttore.html')

# Modifica un produttore esistente
@app.route('/modifica_produttore/<int:produttore_id>', methods=['GET', 'POST'])
def modifica_produttore(produttore_id):
    conn = get_db_connection()
    
    # Recupera il produttore dal database
    produttore = conn.execute('SELECT * FROM produttori WHERE id = ?', (produttore_id,)).fetchone()
    if produttore is None:
        conn.close()
        return 'Produttore non trovato', 404

    # Convertire il risultato in un dizionario per modificarlo
    produttore = dict(produttore)
    
    if request.method == 'POST':
        # Ricevi i dati modificati dal form
        nome_produttore = request.form['nome_produttore']
        indirizzo_produttore = request.form['indirizzo_produttore']

        # Esegui l'aggiornamento nel database
        conn.execute('''
            UPDATE produttori
            SET nome_produttore = ?, indirizzo_produttore = ?
            WHERE id = ?
        ''', (nome_produttore, indirizzo_produttore, produttore_id))
        conn.commit()
        conn.close()

        flash('Produttore aggiornato con successo!', 'success')
        # Reindirizza alla lista dei produttori dopo la modifica
        return redirect(url_for('lista_produttori'))
    
    conn.close()
    # Passa i dati al template
    return render_template('modifica_produttore.html', produttore=produttore)

# Lista Impianti: Visualizza tutti gli impianti
@app.route('/impianti', methods=['GET'])
def lista_impianti():
    # Ottieni il parametro di ricerca 'query' dalla richiesta GET (se esiste)
    query = request.args.get('query', '')

    conn = get_db_connection()

    # Se c'è una query, filtra gli impianti per nome
    if query:
        impianti = conn.execute('''
            SELECT * FROM impianti
            WHERE nome_impianto LIKE ?
        ''', ('%' + query + '%',)).fetchall()
    else:
        # Se non c'è query, restituisci tutti gli impianti
        impianti = conn.execute('SELECT * FROM impianti').fetchall()

    conn.close()

    # Passa i dati alla template per la visualizzazione
    return render_template('lista_impianti.html', impianti=impianti, query=query)

# Aggiungi Impianto
@app.route('/aggiungi_impianto', methods=['GET', 'POST'])
def aggiungi_impianto():
    if request.method == 'POST':
        nome_impianto = request.form['nome_impianto']
        indirizzo_impianto = request.form['indirizzo_impianto']

        with get_db_connection() as conn:
            conn.execute('INSERT INTO impianti (nome_impianto, indirizzo_impianto) VALUES (?, ?)',
                         (nome_impianto, indirizzo_impianto))
            conn.commit()

        flash('Impianto aggiunto con successo!', 'success')

        return redirect(url_for('lista_impianti'))

    return render_template('aggiungi_impianto.html')

# Modifica un impianto esistente
@app.route('/modifica_impianto/<int:impianto_id>', methods=['GET', 'POST'])
def modifica_impianto(impianto_id):
    conn = get_db_connection()
    
    # Recupera l'impianto dal database
    impianto = conn.execute('SELECT * FROM impianti WHERE id = ?', (impianto_id,)).fetchone()
    if impianto is None:
        conn.close()
        return 'Impianto non trovato', 404

    # Convertire il risultato in un dizionario per modificarlo
    impianto = dict(impianto)
    
    if request.method == 'POST':
        # Ricevi i dati modificati dal form
        nome_impianto = request.form['nome_impianto']
        indirizzo_impianto = request.form['indirizzo_impianto']

        # Esegui l'aggiornamento nel database
        conn.execute('''
            UPDATE impianti
            SET nome_impianto = ?, indirizzo_impianto = ?
            WHERE id = ?
        ''', (nome_impianto, indirizzo_impianto, impianto_id))
        conn.commit()
        conn.close()

        flash('Impianto aggiornato con successo!', 'success')
        # Reindirizza alla lista degli impianti dopo la modifica
        return redirect(url_for('lista_impianti'))
    
    conn.close()
    # Passa i dati al template
    return render_template('modifica_impianto.html', impianto=impianto)


# Lista cassoni
@app.route('/cassoni', methods=['GET'])
def lista_cassoni():
    query = request.args.get('query', '')
    conn = get_db_connection()

    if query:
        cassoni = conn.execute('''
            SELECT * FROM cassoni WHERE
            nome_cliente LIKE ? OR
            cantiere_destinazione LIKE ? OR
            tipologia_cassone LIKE ? OR
            altezza_cassone LIKE ?
        ''', ('%' + query + '%',) * 4).fetchall()
    else:
        cassoni = conn.execute('SELECT * FROM cassoni').fetchall()

    conn.close()

    # Convertire le date in oggetti datetime
    cassoni_formattati = []
    for cassone in cassoni:
        cassone = dict(cassone)
        cassone['data_consegna'] = convert_date(cassone.get('data_consegna'))
        cassone['data_ritiro'] = convert_date(cassone.get('data_ritiro'))
        cassoni_formattati.append(cassone)

    return render_template('lista_cassoni.html', cassoni=cassoni_formattati, query=query)

@app.route('/aggiungi_cassone', methods=['GET', 'POST'])
def aggiungi_cassone():
    conn = get_db_connection()
    produttori = conn.execute('SELECT * FROM produttori').fetchall()
    conn.close()

    if request.method == 'POST':
        nome_cliente = request.form['nome_cliente']
        cantiere_destinazione = request.form['cantiere_destinazione']
        tipologia_cassone = request.form['tipologia_cassone']
        altezza_cassone = request.form['altezza_cassone']
        data_consegna = request.form['data_consegna']
        data_ritiro = request.form.get('data_ritiro')
        nome_referente = request.form['nome_referente']
        numero_telefono = request.form['numero_telefono']

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO cassoni (nome_cliente, cantiere_destinazione, tipologia_cassone, altezza_cassone,
                                 data_consegna, data_ritiro, nome_referente, numero_telefono)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (nome_cliente, cantiere_destinazione, tipologia_cassone, altezza_cassone,
              data_consegna, data_ritiro, nome_referente, numero_telefono))
        conn.commit()
        conn.close()

        flash('Cassone aggiunto con successo!', 'success')
        return redirect(url_for('lista_cassoni'))

    # Passa la lista dei produttori al template
    return render_template('aggiungi_cassone.html', produttori=produttori)

@app.route('/modifica_cassone/<int:cassone_id>', methods=['GET', 'POST'])
def modifica_cassone(cassone_id):
    conn = get_db_connection()
    cassone = conn.execute('SELECT * FROM cassoni WHERE id = ?', (cassone_id,)).fetchone()
    produttori = conn.execute('SELECT * FROM produttori').fetchall()

    if not cassone:
        conn.close()
        return 'Cassone non trovato', 404

    if request.method == 'POST':
        nome_cliente = request.form['nome_cliente']
        cantiere_destinazione = request.form['cantiere_destinazione']
        tipologia_cassone = request.form['tipologia_cassone']
        altezza_cassone = request.form['altezza_cassone']
        data_consegna = request.form['data_consegna']
        data_ritiro = request.form.get('data_ritiro')
        nome_referente = request.form['nome_referente']
        numero_telefono = request.form['numero_telefono']

        conn.execute('''
            UPDATE cassoni SET nome_cliente = ?, cantiere_destinazione = ?, tipologia_cassone = ?,
                               altezza_cassone = ?, data_consegna = ?, data_ritiro = ?, 
                               nome_referente = ?, numero_telefono = ?
            WHERE id = ?
        ''', (nome_cliente, cantiere_destinazione, tipologia_cassone, altezza_cassone,
              data_consegna, data_ritiro, nome_referente, numero_telefono, cassone_id))
        conn.commit()
        conn.close()

        flash('Cassone modificato con successo!', 'success')
        return redirect(url_for('lista_cassoni'))

    cassone = dict(cassone)
    cassone['data_consegna'] = convert_date(cassone.get('data_consegna'))
    cassone['data_ritiro'] = convert_date(cassone.get('data_ritiro'))

    conn.close()
    return render_template('modifica_cassone.html', cassone=cassone, produttori=produttori)


# Ricerca documenti
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query') or ""
    conn = get_db_connection()
    documenti = conn.execute('''SELECT * FROM documenti WHERE
        nome_produttore LIKE ? OR impianto_destinazione LIKE ? OR indirizzo_cantiere LIKE ? OR codice_eer LIKE ?''',
        ('%' + query + '%',) * 4).fetchall()
    conn.close()
    return render_template('search.html', documenti=documenti)


@app.route('/ricerca', methods=['GET'])
def ricerca_generale():
    query = request.args.get('query', '').strip()
    conn = get_db_connection()

    # Recupera tutti i dati per la ricerca avanzata
    omologhe_raw = conn.execute('SELECT * FROM documenti').fetchall()
    cassoni_raw = conn.execute('SELECT * FROM cassoni').fetchall()

    conn.close()

    # Converte i risultati in liste di dizionari
    def format_results(results, date_fields):
        formatted = []
        for row in results:
            row_dict = dict(row)
            for field in date_fields:
                if row_dict.get(field):
                    row_dict[field] = convert_date(row_dict[field])
            formatted.append(row_dict)
        return formatted

    omologhe = format_results(omologhe_raw, ['data_invio', 'data_accettazione', 'data_scadenza'])
    cassoni = format_results(cassoni_raw, ['data_consegna', 'data_ritiro'])

    # Se l'utente ha inserito una query, filtra i risultati
    if query:
        def filter_results(results, fields):
            return [
                result for result in results
                if any(query.lower() in str(result[field]).lower() for field in fields)
            ]

        # Filtra le omologhe
        omologhe = filter_results(omologhe, ['nome_produttore'])

        # Filtra i cassoni
        cassoni = filter_results(cassoni, [
            'nome_cliente', 'cantiere_destinazione', 'tipologia_cassone', 
            'altezza_cassone', 'nome_referente', 'numero_telefono'
        ])

    # Funzione per ottenere corrispondenze fuzzy (opzionale)
    def fuzzy_filter(results, fields):
        from fuzzywuzzy import process  # Assicurati che fuzzywuzzy sia installato
        all_values = [
            (field, str(result[field]))
            for result in results for field in fields if field in result
        ]
        matches = process.extract(query, [val[1] for val in all_values], limit=5)
        matched_values = [value for value, score in matches if score > 50]  # Soglia 50
        return [
            result for result in results
            if any(result[field] in matched_values for field in fields if field in result)
        ]

    # Applica il filtro fuzzy se necessario (facoltativo)
    if not omologhe:
        omologhe = fuzzy_filter(omologhe_raw, ['nome_produttore'])
    if not cassoni:
        cassoni = fuzzy_filter(cassoni_raw, [
            'nome_cliente', 'cantiere_destinazione', 'tipologia_cassone', 
            'altezza_cassone', 'nome_referente', 'numero_telefono'
        ])

    # Passa la data attuale al template per confronti
    now = datetime.now()

    return render_template(
        'ricerca_generale.html',
        query=query,
        omologhe=omologhe,
        cassoni=cassoni,
        now=now
    )

# Eliminazione dei documenti selezionati
@app.route('/delete', methods=['POST'])
def delete_documents():
    # Recuperiamo gli ID dei documenti selezionati
    selected_ids = request.form.getlist('document_ids')

    if selected_ids:
        try:
            conn = get_db_connection()
            conn.execute(f"DELETE FROM documenti WHERE id IN ({','.join('?' for _ in selected_ids)})", selected_ids)
            conn.commit()
            conn.close()

            # Invia un'email di notifica (opzionale)
            documenti_eliminati = ', '.join(selected_ids)
            subject = "Notifica di Eliminazione Documenti"
            body = f"I seguenti documenti sono stati eliminati: {documenti_eliminati}"
            send_email(subject, body)

            flash('Documenti eliminati con successo!', 'success')
        except Exception as e:
            flash(f"Errore durante l'eliminazione: {str(e)}", 'danger')
    else:
        flash('Nessun documento selezionato per l\'eliminazione', 'warning')

    return redirect(url_for('lista_omologhe'))

@app.route('/delete_impianti', methods=['POST'])
def delete_impianti():
    # Ottieni gli ID degli impianti selezionati dal form
    impianto_ids = request.form.getlist('impianto_ids')
    conn = get_db_connection()
    if impianto_ids:
        for id in impianto_ids:
            conn.execute('DELETE FROM impianti WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        flash('Impianti eliminati con successo!', 'success')
    else:
        flash('Nessun impianto selezionato per l\'eliminazione', 'warning')

    return redirect(url_for('lista_impianti'))

@app.route('/delete_produttori', methods=['POST'])
def delete_produttori():
    # Ottieni gli ID dei produttori selezionati dal form
    produttore_ids = request.form.getlist('produttore_ids')
    conn = get_db_connection()

    if produttore_ids:
        for id in produttore_ids:
            conn.execute('DELETE FROM produttori WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        flash('Produttori eliminati con successo!', 'success')
    else:
        flash('Nessun produttore selezionato per l\'eliminazione', 'warning')

    return redirect(url_for('lista_produttori'))

@app.route('/elimina_cassone', methods=['POST'])
def elimina_cassone():
    cassone_ids = request.form.getlist('cassone_ids')
    if cassone_ids:
        conn = get_db_connection()
        query = 'DELETE FROM cassoni WHERE id IN ({})'.format(','.join('?' for _ in cassone_ids))
        conn.execute(query, cassone_ids)
        conn.commit()
        conn.close()
        flash('Cassoni eliminati con successo!', 'success')
    else:
        flash('Nessun cassone selezionato per l\'eliminazione.', 'warning')
    return redirect(url_for('lista_cassoni'))

if __name__ == '__main__':
    # Utilizzo di HTTPS con un certificato autofirmato
    context = ('cert.pem', 'key.pem')  # Assicurati di avere questi file
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=context)
